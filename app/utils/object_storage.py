from uuid import UUID

import aioboto3
from botocore.client import Config
from botocore.exceptions import ClientError

from app.core.exceptions.object_storage import (
    ObjectDeleteError,
    ObjectListGetError,
    ObjectUploadError,
)
from app.core.logger import app_logger


class ObjectStorageService:
    """
    Сервис для работы с объектным хранилищем (S3-совместимым).
    Обеспечивает загрузку, удаление и управление аватарками пользователей.

    Использует асинхронный клиент `aioboto3` для взаимодействия с S3.
    """

    def __init__(
        self,
        endpoint_url: str,
        access_key_id: str,
        secret_access_key: str,
        bucket_name: str,
    ):
        """
        Инициализирует сервис с параметрами подключения к S3.

        Args:
            endpoint_url: URL эндпоинта S3 (например, 'https://s3.example.com')
            access_key_id: Идентификатор ключа доступа
            secret_access_key: Секретный ключ доступа
            bucket_name: Имя бакета для хранения файлов
        """
        self.endpoint_url = endpoint_url
        self.bucket_name = bucket_name
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.session = aioboto3.Session()
        self.config = Config(signature_version="s3v4")

    async def _get_client(self):
        """
        Возвращает асинхронный S3-клиент с настроенными параметрами подключения.

        Returns:
            AioBaseClient: Асинхронный клиент для работы с S3
        """
        return self.session.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
            config=self.config,
        )

    async def upload_avatar(self, profile_id: UUID, file_data: bytes) -> str:
        """
        Загружает аватарку пользователя в объектное хранилище.

        Args:
            profile_id: Идентификатор профиля
            file_data: Двоичные данные файла аватарки (ожидается JPEG)

        Returns:
            str: Предподписанный URL для доступа к загруженной аватарке

        Raises:
            ObjectUploadError: Если произошла ошибка при загрузке
        """
        try:
            key = f"users/{profile_id}.jpg"

            async with await self._get_client() as s3:
                await s3.put_object(
                    Bucket=self.bucket_name,
                    Key=key,
                    Body=file_data,
                    ContentType="image/jpeg",
                    Metadata={"profile_id": str(profile_id)},
                )
                app_logger.info(f"Аватарка для профиля {profile_id} успешно загружена")

                return await self._generate_presigned_url(s3, key)
        except ClientError as e:
            app_logger.error(
                f"Ошибка при загрузке аватарки для профиля {profile_id}: {e}"
            )
            raise ObjectUploadError(f"avatar_{profile_id}")

    async def delete_avatar(self, profile_id: UUID) -> None:
        """
        Удаляет аватарку пользователя из объектного хранилища.

        Args:
            profile_id: Идентификатор профиля

        Raises:
            ObjectDeleteError: Если произошла ошибка при удалении
        """
        try:
            key = f"users/{profile_id}.jpg"
            async with await self._get_client() as s3:
                await s3.delete_object(Bucket=self.bucket_name, Key=key)
                app_logger.info(f"Аватарка для профиля {profile_id} успешно удалена")
        except ClientError as e:
            app_logger.error(
                f"Ошибка при удалении аватарки для профиля {profile_id}: {e}"
            )
            raise ObjectDeleteError(f"avatar_{profile_id}")

    async def get_avatar_url(self, profile_id: UUID) -> str | None:
        """
        Возвращает предподписанный URL для доступа к аватарке пользователя.

        Args:
            profile_id: Идентификатор профиля

        Returns:
            str | None: Предподписанный URL или None, если аватарка не найдена
        """
        try:
            key = f"users/{profile_id}.jpg"
            async with await self._get_client() as s3:
                await s3.head_object(Bucket=self.bucket_name, Key=key)

                return await self._generate_presigned_url(s3, key)
        except ClientError as e:
            app_logger.error(
                f"Ошибка при получении URL аватарки для профиля {profile_id}: {e}"
            )
            return None

    async def avatar_exists(self, profile_id: UUID) -> bool:
        """
        Проверяет существование аватарки для указанного профиля.

        Args:
            profile_id: Идентификатор профиля

        Returns:
            bool: True, если аватарка существует, иначе False
        """
        try:
            key = f"users/{profile_id}.jpg"
            async with await self._get_client() as s3:
                await s3.head_object(Bucket=self.bucket_name, Key=key)

                return True
        except ClientError as e:
            app_logger.error(
                f"Ошибка при проверке существования аватарки для профиля {profile_id}: {e}"
            )
            return False

    async def list_avatars(self, profile_ids: list[UUID]) -> dict[UUID, str | None]:
        """
        Возвращает предподписанные URL для аватарок списка профилей.

        Args:
            profile_ids: Список идентификаторов профилей

        Returns:
            dict[UUID, str | None]: Словарь {profile_id: avatar_url} для существующих аватарок

        Raises:
            ObjectListGetError: Если произошла ошибка при получении списка
        """
        try:
            keys = [f"users/{profile_id}.jpg" for profile_id in profile_ids]
            async with await self._get_client() as s3:
                response = await s3.list_objects_v2(
                    Bucket=self.bucket_name, Prefix="users/"
                )

                existing_keys = {obj["Key"] for obj in response.get("Contents", [])}
                result = {}

                for profile_id, key in zip(profile_ids, keys):
                    if key in existing_keys:
                        result[profile_id] = await self._generate_presigned_url(s3, key)
                    else:
                        result[profile_id] = None

                return result
        except ClientError as e:
            app_logger.error(f"Ошибка при получении списка аватарок: {e}")
            raise ObjectListGetError("avatar")

    async def _generate_presigned_url(
        self, s3_client, key: str, expires_in: int = 3600
    ) -> str:
        """
        Генерирует предподписанный URL для доступа к объекту в S3.

        Args:
            s3_client: Асинхронный S3-клиент
            key: Ключ объекта в бакете
            expires_in: Время жизни URL в секундах (по умолчанию: 3600)

        Returns:
            str: Предподписанный URL для доступа к объекту
        """
        return await s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket_name, "Key": key},
            ExpiresIn=expires_in,
        )
