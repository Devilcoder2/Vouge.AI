import asyncio
import sys
import uuid
from pathlib import Path
from datetime import datetime, timezone, timedelta
import random

# Add root folder to python path for standard execution
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from sqlalchemy import select, delete, text
from app.database.session import get_db, async_engine, Base
from app.database.models import (
    User, SocialPost, PostTaggedItem, PostLike, PostComment, PostSave, UserFollow, ClothingItem, FashionCommunity
)

# Stunning curated Unsplash fashion URLs
FASHION_IMAGES = [
    "https://images.unsplash.com/photo-1593030761757-71fae45fa0e7?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1509631179647-0177331693ae?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1529139574466-a303027c1d8b?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1505022610485-0249ba5b3675?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1496747611176-843222e1e57c?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1583743814966-8936f5b7be1a?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1534030347209-467a5b0ad3e6?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1479064555552-3ef4979f8908?auto=format&fit=crop&w=800&q=80"
]

OCCASIONS = ["Work / Office", "Date Night", "Casual Outing", "Evening Gala", "Everyday Casual"]
WEATHERS = ["Mild (15°C)", "Cold (8°C)", "Warm (22°C)", "Rainy (12°C)", "Hot (30°C)"]
PERSONAS = ["minimalist", "quiet_luxury", "streetwear", "techwear", "avant_garde", "vintage"]

async def seed_data():
    print("Hydrating database with Instagram-Style Vogue.AI Social seed data...")
    
    async with async_engine.begin() as conn:
        # Step 1: Safe Table Purge (Clear existing social tables to avoid PK issues)
        print("Clearing existing social records...")
        await conn.execute(text("TRUNCATE TABLE post_comments CASCADE;"))
        await conn.execute(text("TRUNCATE TABLE post_likes CASCADE;"))
        await conn.execute(text("TRUNCATE TABLE post_saves CASCADE;"))
        await conn.execute(text("TRUNCATE TABLE post_tagged_items CASCADE;"))
        await conn.execute(text("TRUNCATE TABLE recreated_fits CASCADE;"))
        await conn.execute(text("TRUNCATE TABLE social_posts CASCADE;"))
        await conn.execute(text("TRUNCATE TABLE user_follows CASCADE;"))
        await conn.execute(text("TRUNCATE TABLE fashion_communities CASCADE;"))
        await conn.execute(text("DELETE FROM users WHERE id != '00000000-0000-0000-0000-000000000001';"))

    # Obtain session
    db_gen = get_db()
    db = await db_gen.__anext__()

    try:
        # Check if default user exists, if not create it
        res = await db.execute(select(User).where(User.id == uuid.UUID("00000000-0000-0000-0000-000000000001")))
        curator = res.scalar_one_or_none()
        
        if curator:
            curator.username = "social_curator"
            curator.vanity_username = "Alex Thorne"
            curator.bio = "Minimalist monochrome fits | Quiet luxury | NYC"
            curator.avatar_url = "https://lh3.googleusercontent.com/aida-public/AB6AXuCUhrbSCCyvL4gMnA4wJKdCIy8rVXkUi-RbzyXY0huiYdfDG1hbrZTi-unXTQtHZr7f0ylpE97bhRPNcOAuBoGKXLZ9h6MkdQTX2Ta77wOdUoQSSmQB-gtnME4J5WbRKBfLHRHGbjQ9nvppXanviB6KFDGHhH3UASuuDBy4oIWLee_5z-H844_4Mt1y2nDji5MV2TT9xd2rZAt5yi9SC4sfotZz_y65OxC_DpSb0DD2ZGoAr5G5CWtbh_ouFF8GyRaY91qgXtX9DUof"
            curator.verified_badge = True
            curator.favorite_brands = ["COS", "Zara", "Uniqlo", "Rick Owens"]
            curator.wardrobe_visibility = "public"
        else:
            curator = User(
                id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                email="alex.thorne@vouge.ai",
                hashed_password="mock_password_hash",
                username="social_curator",
                vanity_username="Alex Thorne",
                bio="Minimalist monochrome fits | Quiet luxury | NYC",
                avatar_url="https://lh3.googleusercontent.com/aida-public/AB6AXuCUhrbSCCyvL4gMnA4wJKdCIy8rVXkUi-RbzyXY0huiYdfDG1hbrZTi-unXTQtHZr7f0ylpE97bhRPNcOAuBoGKXLZ9h6MkdQTX2Ta77wOdUoQSSmQB-gtnME4J5WbRKBfLHRHGbjQ9nvppXanviB6KFDGHhH3UASuuDBy4oIWLee_5z-H844_4Mt1y2nDji5MV2TT9xd2rZAt5yi9SC4sfotZz_y65OxC_DpSb0DD2ZGoAr5G5CWtbh_ouFF8GyRaY91qgXtX9DUof",
                verified_badge=True,
                favorite_brands=["COS", "Zara", "Uniqlo", "Rick Owens"],
                wardrobe_visibility="public"
            )
            db.add(curator)
            
        await db.commit()
        await db.refresh(curator)

        # Ensure we have default categories
        # Seed default clothing items for tagging anchors if empty
        item_res = await db.execute(select(ClothingItem).limit(10))
        clothing_items = item_res.scalars().all()
        
        if not clothing_items:
            print("Seeding baseline closet garments for coordinate hotspot matching...")
            tops = ClothingItem(
                id=uuid.uuid4(),
                user_id="default_user",
                category="tops",
                subcategory="White Shirt",
                primary_color="White",
                textile="Poplin Cotton",
                name="Essential White Shirt",
                occasion="work",
                verified=True,
                categories=["tops"]
            )
            bottoms = ClothingItem(
                id=uuid.uuid4(),
                user_id="default_user",
                category="bottoms",
                subcategory="Charcoal Trousers",
                primary_color="Grey",
                textile="Worsted Wool",
                name="Tapered Wool Trousers",
                occasion="work",
                verified=True,
                categories=["bottoms"]
            )
            outer = ClothingItem(
                id=uuid.uuid4(),
                user_id="default_user",
                category="outerwear",
                subcategory="Trench Coat",
                primary_color="Beige",
                textile="Wool Blend",
                name="Cashmere Wool Trench",
                occasion="formal",
                verified=True,
                categories=["outerwear"]
            )
            db.add_all([tops, bottoms, outer])
            await db.commit()
            clothing_items = [tops, bottoms, outer]

        # Step 2: Seed remaining 9 styled Creators
        creators = [curator]
        names = [
            ("quiet_luxury_edits", "Elena Rostova", "Neutral tailoring | Premium knitwear styling | London", ["COS", "Loro Piana"], True),
            ("tokyo_streetwear", "Kenji Sato", "Oversized silhouettes | Techwear layering | Harajuku", ["Rick Owens", "Y-3", "Nike"], False),
            ("old_money_tailoring", "Alessandro Rossi", "Classic sartorial styling | Tweed & Double-breasted | Milan", ["Brunello Cucinelli", "Ralph Lauren"], True),
            ("minimalist_vibes", "Astrid Lind", "Less is more | Architectural shapes | Stockholm", ["COS", "Acne Studios"], False),
            ("retro_chic_vintage", "Camille Moreau", "70s tailoring & leather coats | Circular fashion | Paris", ["Saint Laurent", "Levi's"], True),
            ("avant_garde_drape", "Yuji Yamamoto", "Asymmetrical structures | Darkwear drapes | Berlin", ["Yohji Yamamoto", "Rick Owens"], False),
            ("techwear_layering", "Marcus Vance", "Gore-tex coordinate systems | Urban utility | Vancouver", ["Arc'teryx", "Nike ACG"], False),
            ("boho_summer_vibes", "Siena Gomez", "Linen drape layering | Earthy tones | Ibiza", ["Zara", "Loewe"], False),
            ("capsule_closet_ideas", "Chloe Chen", "15 items, 100 outfits | Smart capsule builder | Toronto", ["Uniqlo", "Oak + Fort"], True)
        ]

        for username, vanity, bio, brands, verified in names:
            user_id = uuid.uuid4()
            new_creator = User(
                id=user_id,
                email=f"{username}@vouge.ai",
                hashed_password="mock_password_hash",
                username=username,
                vanity_username=vanity,
                bio=bio,
                avatar_url=f"https://api.dicebear.com/7.x/initials/svg?seed={username}",
                verified_badge=verified,
                favorite_brands=brands,
                wardrobe_visibility="public"
            )
            db.add(new_creator)
            creators.append(new_creator)
            
        await db.commit()
        print(f"✓ Seeded 10 Creators (including default @social_curator).")

        # Step 3: Seed Fashion Communities
        minimalist_comm = FashionCommunity(
            id=uuid.uuid4(),
            name="Minimalist Uniform",
            slug="minimalist-uniform",
            description="Architectural shapes, neutral palettes, quiet luxury luxury layering, and capsule closet capsule ideas.",
            cover_image_url="https://images.unsplash.com/photo-1490481651871-ab68de25d43d?auto=format&fit=crop&w=800&q=80",
            rules="1. Only neutral color tones.\n2. Focus on textile and drape.",
            creator_id=curator.id
        )
        streetwear_comm = FashionCommunity(
            id=uuid.uuid4(),
            name="Streetwear Layering",
            slug="streetwear-layering",
            description="Oversized shapes, drop shoulders, cargo utilities, premium sneakers, and avant-garde drapes.",
            cover_image_url="https://images.unsplash.com/photo-1516257984-b1b4d707412e?auto=format&fit=crop&w=800&q=80",
            rules="1. Focus on silhouette and volume proportions.\n2. Respect authentic designers.",
            creator_id=curator.id
        )
        db.add_all([minimalist_comm, streetwear_comm])
        await db.commit()

        # Step 4: Seed 5-10 Posts per User (total 65 posts)
        all_posts = []
        captions = [
            "Worsted wool tailoring drape coordinates layered over poplin shirt. Perfect autumn morning look.",
            "Neutral cashmere wrap trench coat paired with warm calfskin boots. Minimalist drapes.",
            "Oversized cargo streetwear coordinate system layered under yellow street jacket. Harajuku layout.",
            "Classic tweed blazer with rolled sleeve cuffs matching high rise pleated trousers.",
            "Organized organic linen capsule dress styled for warm coastal climate evenings.",
            "Obsidian black drop shoulder basic crewneck paired with heavy cotton relaxed drape pants.",
            "Structured double-breasted double-face cashmere coat layered over structured knitwear.",
            "Asymmetrical linen summer coat with tailored structural coordination details.",
            "Rainy weather technical coordinates featuring gore-tex shell and nylon utility layers."
        ]

        for creator in creators:
            post_count = random.randint(6, 9)
            for i in range(post_count):
                post_id = uuid.uuid4()
                img_url = FASHION_IMAGES[(creator.username.__hash__() + i) % len(FASHION_IMAGES)]
                
                new_post = SocialPost(
                    id=post_id,
                    user_id=creator.id,
                    image_url=img_url,
                    caption=random.choice(captions) + f" (Style coordinate {i+1} by @{creator.username})",
                    weather_context=random.choice(WEATHERS),
                    occasion_tag=random.choice(OCCASIONS),
                    style_persona=random.choice(PERSONAS),
                    created_at=datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 240)),
                    community_id=minimalist_comm.id if i % 3 == 0 else (streetwear_comm.id if i % 3 == 1 else None)
                )
                db.add(new_post)
                all_posts.append(new_post)
                
                # Tag 1-2 random closet garments coordinates in post
                tag_count = random.randint(1, 2)
                for j in range(tag_count):
                    matched_clothing = clothing_items[j % len(clothing_items)]
                    tagged_item = PostTaggedItem(
                        id=uuid.uuid4(),
                        post_id=post_id,
                        wardrobe_item_id=matched_clothing.id,
                        x_coord=random.randint(30, 70),
                        y_coord=random.randint(25, 75)
                    )
                    db.add(tagged_item)

        await db.commit()
        print(f"✓ Seeded {len(all_posts)} Outfit Posts with garment hotspots coordinate tags.")

        # Step 5: Seed Follow Graphs
        # curator follows creators[1], creators[2], creators[4], creators[9]
        # creators[1], creators[2], creators[3], creators[4], creators[5] follow curator (followers list)
        follow_pairs = [
            # Curator following others
            (curator.id, creators[1].id),
            (curator.id, creators[2].id),
            (curator.id, creators[3].id),
            (curator.id, creators[4].id),
            (curator.id, creators[9].id),
            # Others following curator
            (creators[1].id, curator.id),
            (creators[2].id, curator.id),
            (creators[3].id, curator.id),
            (creators[4].id, curator.id),
            (creators[5].id, curator.id),
            (creators[6].id, curator.id)
        ]
        
        # Add random mutual follows between others
        for i in range(1, len(creators)):
            for j in range(1, len(creators)):
                if i != j and random.random() < 0.3:
                    follow_pairs.append((creators[i].id, creators[j].id))

        # Filter out duplicates
        unique_follows = list(set(follow_pairs))
        for follower_id, following_id in unique_follows:
            db.add(UserFollow(follower_id=follower_id, following_id=following_id))

        await db.commit()
        print(f"✓ Seeded follow graphs (Mutual styling network established).")

        # Step 6: Seed Likes & Comments
        comment_contents = [
            "Drape details look extremely high-end! ✨",
            "This silhouette proportion is absolutely perfect.",
            "What fabric blend is that outer coat? Love the textile structure.",
            "Espresso tones coordinates perfectly in worsted wool.",
            "Minimalist uniform goals! Synced directly to my capsule inspo board.",
            "Beautiful layering coordinates. Perfect styling proportions!"
        ]

        # Seed hundreds of likes and comments
        for post in all_posts:
            # Likes
            like_count = random.randint(10, 45)
            likers = random.sample(creators, min(like_count, len(creators)))
            for liker in likers:
                db.add(PostLike(user_id=liker.id, post_id=post.id))
            
            # Saves (only curator saves some posts for saves tab check!)
            if random.random() < 0.3:
                db.add(PostSave(user_id=curator.id, post_id=post.id))

            # Comments
            comm_count = random.randint(1, 4)
            commenters = random.sample(creators, min(comm_count, len(creators)))
            for commenter in commenters:
                db.add(PostComment(
                    id=uuid.uuid4(),
                    user_id=commenter.id,
                    post_id=post.id,
                    content=random.choice(comment_contents),
                    created_at=datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 10))
                ))

        await db.commit()
        print(f"✓ Hydrated social interactions (Likes, Saves, Threaded comments).")
        print("\n🎉 Vogue.AI Social Platform Seeding Completed Successfully! 100% active state generated.")

    except Exception as e:
        await db.rollback()
        print(f"✗ Seeding failed: {str(e)}", file=sys.stderr)
        raise e

if __name__ == "__main__":
    asyncio.run(seed_data())
