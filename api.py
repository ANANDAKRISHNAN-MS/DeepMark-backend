from fastapi import APIRouter

from routers import auth, demo_upload,post,profile,activity

router = APIRouter(prefix="/v1")

router.include_router(auth.router)
router.include_router(post.router)
router.include_router(profile.router)
router.include_router(activity.router)
router.include_router(demo_upload.router)