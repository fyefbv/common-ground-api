from datetime import datetime, timezone

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.exceptions.object_storage import (
    ObjectDeleteError,
    ObjectUploadError,
    ObjectListGetError,
)
from app.core.logger import app_logger


# async def object_not_found_handler(request: Request, exc: ObjectNotFoundError):
#     app_logger.warning(f"Object not found: {exc.detail}")

#     return JSONResponse(
#         status_code=exc.status_code,
#         content={
#             "success": False,
#             "error": {
#                 "code": "object_not_found",
#                 "message": exc.detail,
#                 "timestamp": datetime.now(timezone.utc).isoformat(),
#             },
#         },
#     )


async def object_upload_handler(request: Request, exc: ObjectUploadError):
    app_logger.error(f"Failed to upload object: {exc.detail}")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": "object_upload_error",
                "message": exc.detail,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        },
    )


async def object_delete_handler(request: Request, exc: ObjectDeleteError):
    app_logger.error(f"Failed to delete object: {exc.detail}")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": "object_delete_error",
                "message": exc.detail,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        },
    )


async def object_list_get_handler(request: Request, exc: ObjectListGetError):
    app_logger.error(f"Failed to get object list: {exc.detail}")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": "object_list_get_error",
                "message": exc.detail,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        },
    )
