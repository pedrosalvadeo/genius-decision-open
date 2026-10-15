CREATE TABLE mission_context_forecasts (
 mission_id TEXT PRIMARY KEY REFERENCES adaptive_missions(id) ON DELETE CASCADE,
 request_sha256 TEXT NOT NULL, frozen_json TEXT NOT NULL, forecast_sha256 TEXT NOT NULL,
 frozen_at_us INTEGER NOT NULL, total_count INTEGER NOT NULL CHECK(total_count BETWEEN 9 AND 40),
 report_json TEXT, report_sha256 TEXT,
 CHECK((report_json IS NULL) = (report_sha256 IS NULL))
);
CREATE TABLE mission_context_predictions (
 mission_id TEXT NOT NULL REFERENCES mission_context_forecasts(mission_id) ON DELETE CASCADE,
 sequence INTEGER NOT NULL CHECK(sequence BETWEEN 1 AND 40), prediction_id TEXT NOT NULL,
 request_sha256 TEXT NOT NULL, receipt_json TEXT NOT NULL, receipt_sha256 TEXT NOT NULL,
 issued_at_us INTEGER NOT NULL,
 PRIMARY KEY(mission_id,sequence), UNIQUE(mission_id,prediction_id)
);
CREATE TABLE mission_context_observations (
 mission_id TEXT NOT NULL, sequence INTEGER NOT NULL, observation_id TEXT NOT NULL,
 request_sha256 TEXT NOT NULL, receipt_json TEXT NOT NULL, receipt_sha256 TEXT NOT NULL,
 received_at_us INTEGER NOT NULL,
 PRIMARY KEY(mission_id,sequence), UNIQUE(mission_id,observation_id),
 FOREIGN KEY(mission_id,sequence) REFERENCES mission_context_predictions(mission_id,sequence) ON DELETE CASCADE
);
CREATE TRIGGER mission_context_frozen_immutable
BEFORE UPDATE OF mission_id,request_sha256,frozen_json,forecast_sha256,frozen_at_us,total_count
ON mission_context_forecasts BEGIN SELECT RAISE(ABORT,'context plan is immutable'); END;
CREATE TRIGGER mission_context_report_immutable
BEFORE UPDATE OF report_json,report_sha256 ON mission_context_forecasts
WHEN OLD.report_json IS NOT NULL BEGIN SELECT RAISE(ABORT,'context report is immutable'); END;
CREATE TRIGGER mission_context_predictions_immutable BEFORE UPDATE ON mission_context_predictions
BEGIN SELECT RAISE(ABORT,'context prediction is immutable'); END;
CREATE TRIGGER mission_context_observations_immutable BEFORE UPDATE ON mission_context_observations
BEGIN SELECT RAISE(ABORT,'context observation is immutable'); END;
