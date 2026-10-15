CREATE TABLE mission_forecasts (
 mission_id TEXT PRIMARY KEY REFERENCES adaptive_missions(id) ON DELETE CASCADE,
 request_sha256 TEXT NOT NULL,
 frozen_json TEXT NOT NULL, forecast_sha256 TEXT NOT NULL,
 frozen_at_us INTEGER NOT NULL,
 expected_count INTEGER NOT NULL CHECK(expected_count BETWEEN 3 AND 30),
 report_json TEXT, report_sha256 TEXT,
 CHECK((report_json IS NULL) = (report_sha256 IS NULL))
);
CREATE TABLE mission_forecast_observations (
 mission_id TEXT NOT NULL REFERENCES mission_forecasts(mission_id) ON DELETE CASCADE,
 sequence INTEGER NOT NULL CHECK(sequence BETWEEN 1 AND 30),
 observation_id TEXT NOT NULL, request_sha256 TEXT NOT NULL,
 receipt_json TEXT NOT NULL, receipt_sha256 TEXT NOT NULL,
 received_at_us INTEGER NOT NULL,
 PRIMARY KEY(mission_id,sequence), UNIQUE(mission_id,observation_id)
);
CREATE TRIGGER mission_forecast_frozen_immutable
BEFORE UPDATE OF mission_id,request_sha256,frozen_json,forecast_sha256,frozen_at_us,expected_count
ON mission_forecasts BEGIN SELECT RAISE(ABORT,'frozen forecast is immutable'); END;
CREATE TRIGGER mission_forecast_report_immutable
BEFORE UPDATE OF report_json,report_sha256 ON mission_forecasts
WHEN OLD.report_json IS NOT NULL BEGIN SELECT RAISE(ABORT,'forecast report is immutable'); END;
CREATE TRIGGER mission_forecast_observations_immutable
BEFORE UPDATE ON mission_forecast_observations
BEGIN SELECT RAISE(ABORT,'forecast observation is immutable'); END;
