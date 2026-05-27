"""
Stylist Assistant Chat API — POST /v1/chat/message

Provides a conversational personal stylist chatbot integrated with actual wardrobe pieces
and user styling profiles via Google Gemini AI.
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.config import settings
from app.database.session import get_db
from app.database.models import User, ClothingItem, UserStyleProfile, GeneratedOutfit
from app.schemas.dashboard import ChatMessageRequest, ChatMessageResponse

# Optional Import google-genai
try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

logger = logging.getLogger("fashion-ai-service")
router = APIRouter(prefix="/v1/chat", tags=["Stylist Chat Assistant"])

@router.post("/message", response_model=ChatMessageResponse, status_code=status.HTTP_200_OK)
async def send_stylist_message(
    payload: ChatMessageRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Handles interactive user style assistant queries.
    Uses Gemini to generate custom styling replies, incorporating user style profile and digitized closet.
    """
    logger.info(f"Received stylist query from user={payload.user_id}: '{payload.message}'")
    
    # 1. Resolve user
    user = None
    try:
        user_uuid = uuid.UUID(payload.user_id)
        result = await db.execute(select(User).where(User.id == user_uuid))
        user = result.scalar_one_or_none()
    except ValueError:
        # Fallback to the first user if not a valid UUID
        user_res = await db.execute(select(User).order_by(User.created_at))
        user = user_res.scalars().first()
        
    # 2. Fetch User Style Profile
    profile = None
    profile_desc = ""
    if user:
        profile_res = await db.execute(select(UserStyleProfile).where(UserStyleProfile.user_id == user.id))
        profile = profile_res.scalar_one_or_none()
        
    if profile:
        profile_desc = (
            f"- Preferred Colors: {', '.join(profile.preferred_colors)}\n"
            f"- Disliked Colors: {', '.join(profile.disliked_colors)}\n"
            f"- Preferred Styles: {', '.join(profile.preferred_styles)}\n"
            f"- Favorite Categories: {', '.join(profile.favorite_categories)}\n"
        )
        if profile.color_overreliance_index:
            over = profile.color_overreliance_index
            profile_desc += f"- Color Overreliance Index: {over.get('color_name')} ({over.get('percentage_dependency')}%)\n"
            
    # 3. Fetch Wardrobe pieces
    closet_res = await db.execute(select(ClothingItem))
    items = closet_res.scalars().all()
    
    closet_description = ""
    for idx, item in enumerate(items, 1):
        closet_description += (
            f"{idx}. ID: {item.id} | {item.name or 'Garment'} | "
            f"Category: {item.category} | Subcategory: {item.subcategory} | "
            f"Color: {item.primary_color} | Fit: {item.fit} | Style: {item.style}\n"
        )
        
    # 4. Construct high-fidelity system prompt
    system_prompt = f"""
    You are Vouge.AI Stylist Assistant, a premium, high-end personal AI fashion stylist.
    Your tone is professional, elegant, sophisticated, yet warm and welcoming.
    
    Here is the user's calculated style profile preferences:
    {profile_desc or "No learned style profile compiled yet."}
    
    Here is the user's digitized wardrobe (closet items):
    {closet_description or "Empty closet. Advise them to upload garments so you can style them!"}
    
    Guidelines:
    1. Provide personalized styling advice, outfit recommendations, and answer fashion questions.
    2. Make direct references to their actual closet items where possible. Suggest combining specific items by describing them.
    3. Keep answers elegant, premium, and relatively concise (1-2 paragraphs of stylish commentary).
    4. If you recommend an outfit, specify the IDs of the items recommended.
    """
    
    reply = None
    api_key_configured = settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "YOUR_GEMINI_API_KEY_HERE"
    
    # 5. Invoke Gemini if configured
    if GEMINI_AVAILABLE and api_key_configured:
        try:
            logger.info("Invoking Gemini for personal stylist response...")
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            
            # Build chat history
            contents = []
            for msg in payload.chat_history:
                role = "user" if msg.role == "user" else "model"
                contents.append(types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=msg.content)]
                ))
                
            contents.append(types.Content(
                role="user",
                parts=[types.Part.from_text(text=payload.message)]
            ))
            
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.7
                )
            )
            reply = response.text.strip()
            logger.info("Successfully generated Gemini stylist response.")
        except Exception as gemini_err:
            logger.error(f"Gemini chat styling failed: {gemini_err}. Falling back to premium mocks.")
            
    # 6. Premium mock fallback if Gemini is not available or errored
    if not reply:
        m_lower = payload.message.lower()
        if "rain" in m_lower or "weather" in m_lower or "cloud" in m_lower:
            reply = "With the overcast skies today, I highly recommend layering your charcoal wool trench over the ivory knit. It offers a sophisticated, textured look while keeping you warm and elegant."
        elif "work" in m_lower or "office" in m_lower or "formal" in m_lower:
            reply = "For a polished professional look, let's pair your classic tailored blazer with sleek high-waisted trousers. Adding a subtle neutral boot will keep the silhouette clean and command the room."
        elif "color" in m_lower or "reliance" in m_lower or "navy" in m_lower:
            reply = "I noticed you have a high percentage of Navy tones in your closet. To evolve your style, let's introduce some warm earth tones like camel or olive to add depth and visual interest."
        else:
            reply = "Welcome to your personal Vouge.AI stylist assistant. I am here to help you style your digital wardrobe. Based on your minimalist persona, let's keep your silhouettes sharp and your color palette disciplined."
            
    # 7. Check if we should suggest a cached GeneratedOutfit
    suggested_id = None
    m_lower = payload.message.lower()
    if any(k in m_lower for k in ["suggest", "recommend", "outfit", "wear", "dress"]):
        try:
            outfit_res = await db.execute(
                select(GeneratedOutfit)
                .where(GeneratedOutfit.user_id == str(user.id if user else "default_user"))
                .order_by(GeneratedOutfit.created_at.desc())
            )
            top_outfit = outfit_res.scalars().first()
            if top_outfit:
                suggested_id = str(top_outfit.id)
                logger.info(f"Attached suggested cached outfit ID: {suggested_id}")
        except Exception as outfit_err:
            logger.warning(f"Failed to fetch cached outfit for chat: {outfit_err}")
            
    return ChatMessageResponse(
        reply=reply,
        timestamp=datetime.now(timezone.utc),
        suggested_outfit_id=suggested_id
    )
