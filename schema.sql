-- ============================================================
-- Food Donation Platform - PostgreSQL Schema
-- Run this on your Supabase SQL Editor to initialize the DB
-- ============================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- USERS TABLE
-- Stores all user accounts (donors, NGOs, admins)
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('donor', 'ngo', 'admin')),
    organization_name VARCHAR(150),          -- For NGOs
    phone VARCHAR(20),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- DONATIONS TABLE
-- Food listings posted by donors
-- ============================================================
CREATE TABLE IF NOT EXISTS donations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    donor_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    food_type VARCHAR(50) NOT NULL CHECK (food_type IN ('cooked', 'packaged', 'raw', 'beverages', 'other')),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    quantity_unit VARCHAR(30) DEFAULT 'servings',   -- servings, kg, liters, boxes, etc.
    location TEXT NOT NULL,
    city VARCHAR(100),
    state VARCHAR(100),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    expiry_time TIMESTAMPTZ NOT NULL,
    status VARCHAR(20) DEFAULT 'available' CHECK (status IN ('available', 'claimed', 'expired', 'cancelled')),
    image_url TEXT,
    allergens TEXT,                                 -- e.g., "nuts, dairy"
    pickup_instructions TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- REQUESTS TABLE
-- Claims made by NGOs on available donations
-- ============================================================
CREATE TABLE IF NOT EXISTS requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    donation_id UUID NOT NULL REFERENCES donations(id) ON DELETE CASCADE,
    ngo_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    message TEXT,                                   -- Message from NGO to donor
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'completed')),
    pickup_time TIMESTAMPTZ,                        -- Agreed pickup time
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(donation_id, ngo_id)                     -- One request per NGO per donation
);

-- ============================================================
-- INDEXES for performance
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_donations_donor_id ON donations(donor_id);
CREATE INDEX IF NOT EXISTS idx_donations_status ON donations(status);
CREATE INDEX IF NOT EXISTS idx_donations_city ON donations(city);
CREATE INDEX IF NOT EXISTS idx_donations_expiry ON donations(expiry_time);
CREATE INDEX IF NOT EXISTS idx_requests_donation_id ON requests(donation_id);
CREATE INDEX IF NOT EXISTS idx_requests_ngo_id ON requests(ngo_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- ============================================================
-- AUTO-UPDATE updated_at TRIGGER
-- ============================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_donations_updated_at
    BEFORE UPDATE ON donations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_requests_updated_at
    BEFORE UPDATE ON requests
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- AUTO-EXPIRE DONATIONS (optional scheduled job)
-- Run periodically: UPDATE donations SET status='expired'
-- WHERE expiry_time < NOW() AND status='available';
-- ============================================================

-- ============================================================
-- SEED DATA - Default admin account
-- Password: admin123 (bcrypt hash - change in production!)
-- ============================================================
INSERT INTO users (name, email, password_hash, role)
VALUES (
    'Admin',
    'admin@foodbridge.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeVkVPBH.2WTqN2Ky',
    'admin'
) ON CONFLICT (email) DO NOTHING;
