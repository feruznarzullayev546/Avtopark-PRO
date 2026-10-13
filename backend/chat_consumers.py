"""Authenticated, permission-checked WebSocket consumer for private 1-to-1 chat."""
import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth import get_user_model
from django.utils import timezone

from core.models import ChatConversation, ChatMessage, CompanyMembership, UserProfile


class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get("user")
        try:
            self.other_id = int(self.scope["url_route"]["kwargs"]["user_id"])
        except (KeyError, TypeError, ValueError):
            await self.close(code=4400)
            return

        if not self.user or not self.user.is_authenticated:
            await self.close(code=4401)
            return

        allowed = await self._can_chat(self.user.pk, self.other_id)
        if not allowed:
            await self.close(code=4403)
            return

        self.user_a_id, self.user_b_id = sorted((self.user.pk, self.other_id))
        self.group_name = f"chat.conversation.{self.user_a_id}.{self.user_b_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        group_name = getattr(self, "group_name", None)
        if group_name:
            await self.channel_layer.group_discard(group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            await self.send_json({"type": "error", "error": "Bo‘sh xabar."})
            return
        try:
            payload = json.loads(text_data)
        except (TypeError, json.JSONDecodeError):
            await self.send_json({"type": "error", "error": "Noto‘g‘ri JSON."})
            return

        if payload.get("event") != "message":
            await self.send_json({"type": "error", "error": "Noma’lum chat hodisasi."})
            return

        body = str(payload.get("body", "")).strip()
        if not body:
            await self.send_json({"type": "error", "error": "Xabar bo‘sh bo‘lishi mumkin emas."})
            return
        if len(body) > 5000:
            await self.send_json({"type": "error", "error": "Xabar 5000 belgidan oshmasin."})
            return

        message = await self._create_message(self.user.pk, self.other_id, body)
        if not message:
            await self.send_json({"type": "error", "error": "Suhbatni yaratib bo‘lmadi."})
            return
        await self.channel_layer.group_send(
            self.group_name,
            {"type": "chat.message", "message": message["message"], "conversation_id": message["conversation_id"]},
        )

    async def chat_message(self, event):
        # The React client listens for event.type === 'message'.
        await self.send_json({
            "type": "message",
            "message": event["message"],
            "conversation_id": event.get("conversation_id"),
        })

    @database_sync_to_async
    def _can_chat(self, requester_id, other_id):
        User = get_user_model()
        requester = User.objects.filter(pk=requester_id, is_active=True).first()
        other = User.objects.filter(pk=other_id, is_active=True).first()
        if not requester or not other or requester.pk == other.pk:
            return False

        def is_super(user):
            return bool(user.is_superuser or UserProfile.objects.filter(
                user=user, role=UserProfile.ROLE_SUPER_ADMIN, is_active=True
            ).exists())

        if is_super(requester):
            return True
        if is_super(other):
            return CompanyMembership.objects.filter(
                user=requester,
                status=CompanyMembership.STATUS_ACTIVE,
                role=CompanyMembership.ROLE_DIRECTOR,
            ).exists()

        my_company_ids = CompanyMembership.objects.filter(
            user=requester, status=CompanyMembership.STATUS_ACTIVE
        ).values_list("company_id", flat=True)
        return CompanyMembership.objects.filter(
            user=other,
            status=CompanyMembership.STATUS_ACTIVE,
            company_id__in=my_company_ids,
        ).exists()

    @database_sync_to_async
    def _create_message(self, sender_id, other_id, body):
        User = get_user_model()
        if not self._can_chat_sync(sender_id, other_id):
            return None
        a, b = sorted((sender_id, other_id))
        conversation, _ = ChatConversation.objects.get_or_create(
            user_a_id=a, user_b_id=b, defaults={"company_id": self._shared_company_id(sender_id, other_id)}
        )
        message = ChatMessage.objects.create(
            conversation=conversation,
            sender_id=sender_id,
            body=body,
        )
        return {
            "conversation_id": conversation.pk,
            "message": {
                "id": message.pk,
                "sender_id": message.sender_id,
                "body": message.body,
                "created_at": message.created_at.isoformat(),
                "read_at": None,
            },
        }

    def _can_chat_sync(self, requester_id, other_id):
        User = get_user_model()
        requester = User.objects.filter(pk=requester_id, is_active=True).first()
        other = User.objects.filter(pk=other_id, is_active=True).first()
        if not requester or not other or requester.pk == other.pk:
            return False
        requester_super = requester.is_superuser or UserProfile.objects.filter(
            user=requester, role=UserProfile.ROLE_SUPER_ADMIN, is_active=True
        ).exists()
        other_super = other.is_superuser or UserProfile.objects.filter(
            user=other, role=UserProfile.ROLE_SUPER_ADMIN, is_active=True
        ).exists()
        if requester_super:
            return True
        if other_super:
            return CompanyMembership.objects.filter(
                user=requester, status=CompanyMembership.STATUS_ACTIVE,
                role=CompanyMembership.ROLE_DIRECTOR,
            ).exists()
        company_ids = CompanyMembership.objects.filter(
            user=requester, status=CompanyMembership.STATUS_ACTIVE
        ).values_list("company_id", flat=True)
        return CompanyMembership.objects.filter(
            user=other, status=CompanyMembership.STATUS_ACTIVE, company_id__in=company_ids
        ).exists()

    def _shared_company_id(self, requester_id, other_id):
        return CompanyMembership.objects.filter(
            user_id=requester_id,
            status=CompanyMembership.STATUS_ACTIVE,
            company__memberships__user_id=other_id,
            company__memberships__status=CompanyMembership.STATUS_ACTIVE,
        ).values_list("company_id", flat=True).first()
