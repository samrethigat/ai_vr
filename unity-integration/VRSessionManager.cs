using System;
using System.Collections;
using System.Collections.Generic;
using System.Text;
using UnityEngine;
using UnityEngine.Networking;
using UnityEngine.UI;

namespace FloodShield.VR
{
    /// <summary>
    /// Records trainee drill events (triages, rescues, tool swaps, hazard violations)
    /// and submits the final telemetry stream to the AI Scoring Engine for 8-Vector evaluation.
    /// </summary>
    public class VRSessionManager : MonoBehaviour
    {
        [Header("Backend API Endpoint")]
        [Tooltip("Backend URL for evaluation")]
        public string evaluationUrl = "http://localhost:8000/api/v1/vr/telemetry-evaluate";

        [Header("Session Metadata")]
        public string traineeId = "trainee-rahul-09";
        public string scenarioId = "SCEN_URBAN_DELUGE_01";
        public string scenarioTitle = "Brahmaputra Lowlands Urban Deluge & Substation Isolation";
        public string difficulty = "MEDIUM";
        public int totalVictims = 4;

        [Header("VR Scoreboard UI")]
        public GameObject scoreboardCanvas;
        public Text overallScoreText;
        public Text qualificationTierText;
        public Text safetyScoreText;
        public Text rescueScoreText;
        public Text decisionScoreText;
        public Text adaptiveRecommendationText;

        private float sessionStartTime;
        private int rescuedVictimsCount = 0;
        private int hazardViolationsCount = 0;
        private List<TelemetryEventDTO> telemetryEvents = new List<TelemetryEventDTO>();

        [Serializable]
        public class TelemetryEventDTO
        {
            public float timestamp_sec;
            public float position_x;
            public float position_y;
            public float position_z;
            public float speed;
            public string current_zone;
            public string action_type; // MOVE, TOOL_EQUIP, VICTIM_TRIAGE, VICTIM_RESCUE, HAZARD_EXPOSURE, RADIO_CALL
            public string target_entity;
            public float hazard_proximity_m;
            public string tool_in_hand;
            public string notes;
        }

        [Serializable]
        public class EvaluationRequestPayload
        {
            public string session_id;
            public string trainee_id;
            public string scenario_id;
            public string scenario_title;
            public string difficulty;
            public float total_duration_seconds;
            public int victims_total;
            public int victims_rescued;
            public int hazards_triggered;
            public List<TelemetryEventDTO> telemetry_stream;
        }

        [Serializable]
        public class CompetencyScoresDTO
        {
            public float safety_awareness;
            public float rescue_effectiveness;
            public float decision_quality;
            public float route_efficiency;
            public float response_time;
            public float communication;
            public float tool_usage;
            public float adaptability;
            public float overall_score;
        }

        [Serializable]
        public class NextRecommendationDTO
        {
            public string recommended_scenario_id;
            public string recommended_scenario_title;
            public string difficulty;
            public string rationale;
            public string[] focus_skills;
        }

        [Serializable]
        public class EvaluationResponsePayload
        {
            public string session_id;
            public string trainee_id;
            public string performance_tier;
            public float overall_score;
            public CompetencyScoresDTO competency_scores;
            public string[] strengths;
            public string[] weaknesses;
            public NextRecommendationDTO next_training_recommendation;
        }

        void Start()
        {
            sessionStartTime = Time.time;
            if (scoreboardCanvas != null) scoreboardCanvas.SetActive(false);
        }

        /// <summary>
        /// Call this when a victim is triaged or rescued in Unity.
        /// </summary>
        public void OnVictimRescued(string victimName, Vector3 position)
        {
            rescuedVictimsCount++;
            RecordEvent("VICTIM_RESCUE", victimName, position, 15f);
            Debug.Log($"[FloodShield VR] Rescued {victimName} ({rescuedVictimsCount}/{totalVictims})");
        }

        /// <summary>
        /// Call this when trainee comes dangerously close (<3m) to a hazard.
        /// </summary>
        public void OnHazardViolation(string hazardName, Vector3 position, float distance)
        {
            hazardViolationsCount++;
            RecordEvent("HAZARD_EXPOSURE", hazardName, position, distance);
            Debug.LogWarning($"[FloodShield VR] Hazard violation: {hazardName} at {distance:F1}m!");
        }

        public void RecordEvent(string actionType, string targetEntity, Vector3 position, float hazardDist)
        {
            telemetryEvents.Add(new TelemetryEventDTO
            {
                timestamp_sec = (float)Math.Round(Time.time - sessionStartTime, 1),
                position_x = (float)Math.Round(position.x, 2),
                position_y = (float)Math.Round(position.y, 2),
                position_z = (float)Math.Round(position.z, 2),
                speed = 1.2f,
                current_zone = "Zone_A_Urban",
                action_type = actionType,
                target_entity = targetEntity,
                hazard_proximity_m = (float)Math.Round(hazardDist, 1),
                tool_in_hand = GetComponent<VRTelemetryClient>() != null ? GetComponent<VRTelemetryClient>().equippedTool : "Life Jacket",
                notes = "Auto-recorded via Unity VR rig"
            });
        }

        /// <summary>
        /// Call this when trainee reaches the elevated shelter or time expires.
        /// </summary>
        public void EndDrillAndEvaluate()
        {
            StartCoroutine(PostEvaluationCoroutine());
        }

        private IEnumerator PostEvaluationCoroutine()
        {
            float duration = Time.time - sessionStartTime;

            var payload = new EvaluationRequestPayload
            {
                session_id = $"unity-sess-{Guid.NewGuid().ToString().Substring(0, 8)}",
                trainee_id = traineeId,
                scenario_id = scenarioId,
                scenario_title = scenarioTitle,
                difficulty = difficulty,
                total_duration_seconds = (float)Math.Round(duration, 1),
                victims_total = totalVictims,
                victims_rescued = rescuedVictimsCount,
                hazards_triggered = hazardViolationsCount,
                telemetry_stream = telemetryEvents
            };

            string json = JsonUtility.ToJson(payload);
            byte[] bodyRaw = Encoding.UTF8.GetBytes(json);

            UnityWebRequest req = new UnityWebRequest(evaluationUrl, "POST");
            req.uploadHandler = new UploadHandlerRaw(bodyRaw);
            req.downloadHandler = new DownloadHandlerBuffer();
            req.SetRequestHeader("Content-Type", "application/json");

            Debug.Log("[FloodShield VR] Submitting telemetry to AI Scoring Engine...");
            yield return req.SendWebRequest();

            if (req.result == UnityWebRequest.Result.Success)
            {
                string resText = req.downloadHandler.text;
                Debug.Log($"[FloodShield VR] Evaluation received: {resText}");
                DisplayScoreboard(resText);
            }
            else
            {
                Debug.LogError($"[FloodShield VR] Evaluation failed: {req.error} | {req.downloadHandler.text}");
            }
        }

        private void DisplayScoreboard(string jsonResponse)
        {
            try
            {
                EvaluationResponsePayload result = JsonUtility.FromJson<EvaluationResponsePayload>(jsonResponse);
                if (result == null) return;

                if (scoreboardCanvas != null) scoreboardCanvas.SetActive(true);

                if (overallScoreText != null) overallScoreText.text = $"{result.overall_score:F1} / 100";
                if (qualificationTierText != null) qualificationTierText.text = result.performance_tier;

                if (result.competency_scores != null)
                {
                    if (safetyScoreText != null) safetyScoreText.text = $"Safety Awareness: {result.competency_scores.safety_awareness:F0}%";
                    if (rescueScoreText != null) rescueScoreText.text = $"Rescue Effectiveness: {result.competency_scores.rescue_effectiveness:F0}%";
                    if (decisionScoreText != null) decisionScoreText.text = $"Decision Quality: {result.competency_scores.decision_quality:F0}%";
                }

                if (result.next_training_recommendation != null && adaptiveRecommendationText != null)
                {
                    adaptiveRecommendationText.text = $"Recommended Next Scenario: {result.next_training_recommendation.recommended_scenario_title} ({result.next_training_recommendation.difficulty})";
                }
            }
            catch (Exception ex)
            {
                Debug.LogError($"Scoreboard display error: {ex.Message}");
            }
        }
    }
}
