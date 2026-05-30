-- =============================================================================
-- GPRPANEL — Supabase schema
-- Run this in: https://supabase.com/dashboard/project/sfvwhbzxkzlscfsnyrwq/sql/new
-- =============================================================================

-- Sessions table
-- Each row = one GPR calculation (from browser or CAD plugin)
CREATE TABLE IF NOT EXISTS gpr_sessions (
  id            uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at    timestamptz DEFAULT now(),
  updated_at    timestamptz DEFAULT now(),
  project_name  text,
  site_area     numeric     NOT NULL CHECK (site_area > 0),  -- m²
  plants        jsonb       NOT NULL DEFAULT '[]',
  -- plants schema: [{
  --   species:     text,
  --   common_name: text,
  --   lai_mean:    numeric,
  --   tier:        integer,  (1–4)
  --   canopy_area: numeric   (m²)
  -- }]
  gpr_value     numeric,    -- calculated by Supabase RPC
  source        text        DEFAULT 'manual'
  -- source values: 'manual' | 'autocad' | 'revit' | 'rhino' | 'vectorworks'
);

-- Row-level security (public read/write for PoC — no auth required)
ALTER TABLE gpr_sessions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "public read"   ON gpr_sessions FOR SELECT USING (true);
CREATE POLICY "public insert" ON gpr_sessions FOR INSERT WITH CHECK (true);
CREATE POLICY "public update" ON gpr_sessions FOR UPDATE USING (true);

-- =============================================================================
-- calculate_gpr(session_id)
-- Called by GPRPANEL after saving. Returns the GPR value and writes it back.
-- GPR = Σ(LAI_i × canopy_area_i) / site_area
-- =============================================================================
CREATE OR REPLACE FUNCTION calculate_gpr(p_session_id uuid)
RETURNS numeric
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  sess          gpr_sessions%ROWTYPE;
  plant         jsonb;
  total_lc      numeric := 0;
  gpr_result    numeric;
BEGIN
  SELECT * INTO sess FROM gpr_sessions WHERE id = p_session_id;
  IF NOT FOUND THEN RAISE EXCEPTION 'Session % not found', p_session_id; END IF;

  FOR plant IN SELECT * FROM jsonb_array_elements(sess.plants)
  LOOP
    total_lc := total_lc +
      COALESCE((plant->>'lai_mean')::numeric, 0) *
      COALESCE((plant->>'canopy_area')::numeric, 0);
  END LOOP;

  gpr_result := CASE WHEN sess.site_area > 0 THEN total_lc / sess.site_area ELSE 0 END;

  UPDATE gpr_sessions
    SET gpr_value = gpr_result, updated_at = now()
    WHERE id = p_session_id;

  RETURN gpr_result;
END;
$$;
