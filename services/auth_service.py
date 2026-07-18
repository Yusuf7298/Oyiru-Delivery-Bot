from database.models.user import User
class AuthService:
    def __init__(self, user_repository):
        self.user_repository = user_repository
    async def user_exists(self, telegram_id):
        return await self.user_repository.get_by_telegram_id(
            telegram_id
        )
    async def register_user(
        self,
        telegram_id,
        full_name,
        username,
        phone,
        hotel_id,
    ):
        user = User(
            telegram_id=telegram_id,
            full_name=full_name,
            username=username,
            phone=phone,
            hotel_id=hotel_id,
            role="customer",
        )
        return await self.user_repository.create_user(
            user
        )