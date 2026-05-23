-- PostgreSQL Database Schema Design
-- Target Version: PostgreSQL 15+
-- Architecture: Multi-service database boundaries (defined by schemas or logical separation)
-- Identifier Strategy: UUID v4 (gen_random_uuid) for global uniqueness

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

--------------------------------------------------------------------------------
-- CUSTOM TYPE / ENUM DEFINITIONS
--------------------------------------------------------------------------------

CREATE TYPE processing_status AS ENUM ('pending', 'processed', 'failed');
CREATE TYPE source_type AS ENUM ('upload', 'camera', 'url');
CREATE TYPE outfit_role AS ENUM ('top', 'bottom', 'shoes', 'outerwear', 'accessory');
CREATE TYPE feed_interaction_action AS ENUM ('like', 'save', 'dismiss');
CREATE TYPE budget_band_type AS ENUM ('low', 'medium', 'high', 'luxury');
CREATE TYPE channel_type AS ENUM ('email', 'push', 'sms', 'in_app');

--------------------------------------------------------------------------------
-- 1. USER SERVICE SCHEMA
--------------------------------------------------------------------------------

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(50) UNIQUE,
    auth_provider VARCHAR(50) NOT NULL DEFAULT 'local', -- 'local', 'google', 'apple'
    password_hash VARCHAR(255), -- NULL if using social auth
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_profiles (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    height_cm NUMERIC(5, 2),
    weight_kg NUMERIC(5, 2),
    body_type VARCHAR(50), -- 'hourglass', 'pear', 'inverted_triangle', 'rectangle', 'apple'
    skin_tone VARCHAR(50), -- hex code or profile class
    gender VARCHAR(50), -- user preferred description or self-selected
    dob DATE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_preferences (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    style_tags VARCHAR(100)[] NOT NULL DEFAULT '{}', -- GIN indexed
    disliked_colors VARCHAR(50)[] NOT NULL DEFAULT '{}',
    budget_band budget_band_type NOT NULL DEFAULT 'medium',
    size_top VARCHAR(20),
    size_bottom VARCHAR(20),
    size_shoes VARCHAR(20),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

--------------------------------------------------------------------------------
-- 2. WARDROBE SERVICE SCHEMA
--------------------------------------------------------------------------------

CREATE TABLE wardrobe_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category VARCHAR(100) NOT NULL, -- e.g., 'Tops'
    subcategory VARCHAR(100) NOT NULL, -- e.g., 'T-Shirts & Tanks'
    primary_color VARCHAR(7) NOT NULL, -- Hex code, e.g., '#FFFFFF'
    secondary_colors VARCHAR(7)[] NOT NULL DEFAULT '{}',
    pattern VARCHAR(50) DEFAULT 'solid', -- 'solid', 'striped', 'plaid', etc.
    fit VARCHAR(50) DEFAULT 'standard', -- 'slim', 'standard', 'oversized'
    formality INTEGER NOT NULL CHECK (formality BETWEEN 1 AND 10),
    seasons VARCHAR(20)[] NOT NULL DEFAULT '{}', -- 'spring', 'summer', etc.
    image_url TEXT NOT NULL,
    thumb_url TEXT,
    source source_type NOT NULL DEFAULT 'upload',
    source_url TEXT,
    processing_status processing_status NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE item_attributes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    item_id UUID NOT NULL REFERENCES wardrobe_items(id) ON DELETE CASCADE,
    key VARCHAR(100) NOT NULL, -- e.g., 'fabric', 'neckline', 'sleeve_length'
    value VARCHAR(255) NOT NULL,
    confidence NUMERIC(3, 2) NOT NULL CHECK (confidence BETWEEN 0.00 AND 1.00),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE item_tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    item_id UUID NOT NULL REFERENCES wardrobe_items(id) ON DELETE CASCADE,
    tag VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (item_id, tag)
);

--------------------------------------------------------------------------------
-- 3. OUTFIT SERVICE SCHEMA
--------------------------------------------------------------------------------

CREATE TABLE outfits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    context_json JSONB NOT NULL DEFAULT '{}'::jsonb, -- Weather, occasion, temp
    reasoning_text TEXT, -- Stylist LLM commentary
    score NUMERIC(3, 2) NOT NULL CHECK (score BETWEEN 0.00 AND 1.00),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE outfit_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    outfit_id UUID NOT NULL REFERENCES outfits(id) ON DELETE CASCADE,
    item_id UUID NOT NULL REFERENCES wardrobe_items(id) ON DELETE CASCADE,
    role outfit_role NOT NULL, -- 'top', 'bottom', 'shoes', etc.
    UNIQUE (outfit_id, item_id)
);

CREATE TABLE saved_outfits (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    outfit_id UUID NOT NULL REFERENCES outfits(id) ON DELETE CASCADE,
    saved_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, outfit_id)
);

CREATE TABLE gap_analysis_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    missing_item_description TEXT NOT NULL,
    unlocked_outfit_count INTEGER NOT NULL DEFAULT 0,
    versatility_score NUMERIC(3, 2) NOT NULL CHECK (versatility_score BETWEEN 0.00 AND 1.00),
    suggested_product_ids UUID[] NOT NULL DEFAULT '{}', -- references external_products
    computed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL
);

--------------------------------------------------------------------------------
-- 4. FEED SERVICE SCHEMA
--------------------------------------------------------------------------------

CREATE TABLE feed_cards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    model_image_url TEXT NOT NULL,
    style_tags VARCHAR(100)[] NOT NULL DEFAULT '{}',
    source VARCHAR(100) NOT NULL DEFAULT 'editorial', -- 'editorial', 'partnership'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tagging items physically on a model image (interactive hotspots)
CREATE TABLE feed_card_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    card_id UUID NOT NULL REFERENCES feed_cards(id) ON DELETE CASCADE,
    product_title VARCHAR(255) NOT NULL, -- display title for hotspot
    brand VARCHAR(100),
    role outfit_role NOT NULL,
    x_coord NUMERIC(5, 2) NOT NULL, -- % coordinate from left (0.00 to 100.00)
    y_coord NUMERIC(5, 2) NOT NULL, -- % coordinate from top (0.00 to 100.00)
    external_product_url TEXT -- direct link or resolving affiliate redirect
);

CREATE TABLE user_feed_interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    card_id UUID NOT NULL REFERENCES feed_cards(id) ON DELETE CASCADE,
    action feed_interaction_action NOT NULL, -- 'like', 'save', 'dismiss'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, card_id, action)
);

--------------------------------------------------------------------------------
-- 5. COMMERCE SERVICE SCHEMA
--------------------------------------------------------------------------------

CREATE TABLE external_products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source VARCHAR(100) NOT NULL, -- 'amazon', 'hm', 'myntra', etc.
    source_id VARCHAR(255) NOT NULL, -- Partner item ID
    title VARCHAR(255) NOT NULL,
    brand VARCHAR(100),
    image_url TEXT NOT NULL,
    price NUMERIC(10, 2) NOT NULL,
    currency VARCHAR(10) NOT NULL DEFAULT 'INR',
    url TEXT NOT NULL,
    scraped_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (source, source_id)
);

CREATE TABLE affiliate_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL REFERENCES external_products(id) ON DELETE CASCADE,
    network VARCHAR(100) NOT NULL, -- 'amazon_associates', 'cuelinks', etc.
    tracking_url TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE purchase_clicks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL, -- preserve logs if user deletes account
    product_id UUID NOT NULL REFERENCES external_products(id) ON DELETE CASCADE,
    outfit_id UUID REFERENCES outfits(id) ON DELETE SET NULL, -- optional reference if clicked via outfit
    referrer_context VARCHAR(100) NOT NULL, -- 'feed', 'gap_analysis', 'wardrobe_detail'
    clicked_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

--------------------------------------------------------------------------------
-- 6. NOTIFICATION SERVICE SCHEMA
--------------------------------------------------------------------------------

CREATE TABLE device_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token TEXT NOT NULL,
    platform VARCHAR(50) NOT NULL, -- 'ios', 'android', 'web'
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, token)
);

CREATE TABLE notification_preferences (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    email_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    push_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    sms_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    body TEXT NOT NULL,
    channel channel_type NOT NULL,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb, -- action route, dynamic IDs
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

--------------------------------------------------------------------------------
-- PERFORMANCE INDEXING STRATEGY
--------------------------------------------------------------------------------

-- User indices
CREATE INDEX idx_users_email ON users(email);

-- Wardrobe indices
CREATE INDEX idx_wardrobe_items_user ON wardrobe_items(user_id);
CREATE INDEX idx_wardrobe_items_category_sub ON wardrobe_items(category, subcategory);
CREATE INDEX idx_item_attributes_item ON item_attributes(item_id);
CREATE INDEX idx_item_tags_item ON item_tags(item_id);

-- Outfit indices
CREATE INDEX idx_outfits_user ON outfits(user_id);
CREATE INDEX idx_outfit_items_outfit ON outfit_items(outfit_id);
CREATE INDEX idx_outfit_items_item ON outfit_items(item_id);
CREATE INDEX idx_saved_outfits_user ON saved_outfits(user_id);
CREATE INDEX idx_gap_analysis_user ON gap_analysis_results(user_id);

-- Feed indices
CREATE INDEX idx_feed_card_items_card ON feed_card_items(card_id);
CREATE INDEX idx_user_feed_interactions_user ON user_feed_interactions(user_id);

-- Commerce indices
CREATE INDEX idx_affiliate_links_product ON affiliate_links(product_id);
CREATE INDEX idx_purchase_clicks_user ON purchase_clicks(user_id);
CREATE INDEX idx_purchase_clicks_product ON purchase_clicks(product_id);

-- Notification indices
CREATE INDEX idx_notifications_user_unread ON notifications(user_id) WHERE is_read = FALSE;
CREATE INDEX idx_device_tokens_user ON device_tokens(user_id);

-- GIN indices for highly concurrent Array / JSONB querying
CREATE INDEX idx_user_preferences_style ON user_preferences USING GIN (style_tags);
CREATE INDEX idx_wardrobe_items_seasons ON wardrobe_items USING GIN (seasons);
CREATE INDEX idx_feed_cards_style ON feed_cards USING GIN (style_tags);
CREATE INDEX idx_notifications_payload ON notifications USING GIN (payload);
