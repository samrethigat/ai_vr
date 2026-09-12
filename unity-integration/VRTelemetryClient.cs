using System;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using System.Net.WebSockets;
using UnityEngine;
using UnityEngine.UI;

namespace FloodShield.VR
{
    /// <summary>
    /// Connects Unity VR to the FastAPI Backend via WebSocket.
    /// Streams live head/avatar positions, equipped tool, and hazard proximity at 5-10Hz.
    /// Receives real-time tactical directives and audio cues from the AI Virtual Instructor.
    /// </summary>
    public class VRTelemetryClient : MonoBehaviour
    {
        [Header("Backend Connection")]
        [Tooltip("WebSocket URL. Use ws://localhost:8000 for PC VR, or ws://192.168.x.x:8000 for standalone Meta Quest")]
        public string websocketUrl = "ws://localhost:8000/ws/vr-telemetry";

        [Header("VR Rig References")]
        [Tooltip("Main VR Camera (CenterEyeAnchor / Headset)")]
        public Transform vrHeadset;
        
        [Header("Environment & Equipment")]
        public string equippedTool = "Life Jacket"; // "Insulated Probe", "Rescue Boat", etc.
        public float currentWaterLevel = 0.45f;
        public float waterRiseRate = 0.05f;

        [Header("Tactical VR HUD UI")]
        public Text hudHeadlineText;
        public Text hudActionText;
        public GameObject hudWarningPanel;
        public AudioSource audioSource;
        public AudioClip warningSound;
        public AudioClip alertSound;

        private ClientWebSocket webSocket;
        private CancellationTokenSource cts;
        private float sendTimer = 0f;
        private const float SEND_INTERVAL = 0.15f; // ~6.6 Hz telemetry frequency
        private float drillStartTime;

        // Serializable Telemetry Packet sent to FastAPI
        [Serializable]
        public class OutgoingTelemetryPacket
        {
            public float pos_x;
            public float pos_y;
            public float pos_z;
            public string tool;
            public float water_level_m;
            public float water_rise_rate;
            public string nearest_hazard_type;
            public float nearest_hazard_dist_m;
            public string victim_priority;
            public float victim_dist_m;
            public float timestamp_sec;
            public string zone;
        }

        // Serializable Response Packet from FastAPI Virtual Instructor
        [Serializable]
        public class IncomingInstructorPrompt
        {
            public string priority;
            public string audio_cue_id;
            public string headline;
            public string message;
            public string suggested_action;
            public string safety_rule_code;
        }

        [Serializable]
        public class IncomingInstructorResponse
        {
            public string status;
            public IncomingInstructorPrompt[] prompts;
            public float timestamp;
            public bool warning_active;
        }

        async void Start()
        {
            drillStartTime = Time.time;
            if (vrHeadset == null)
            {
                vrHeadset = Camera.main != null ? Camera.main.transform : transform;
            }

            await ConnectWebSocket();
        }

        async Task ConnectWebSocket()
        {
            try
            {
                cts = new CancellationTokenSource();
                webSocket = new ClientWebSocket();
                Uri serverUri = new Uri(websocketUrl);

                Debug.Log($"[FloodShield VR] Connecting to AI WebSocket at {websocketUrl}...");
                await webSocket.ConnectAsync(serverUri, cts.Token);
                Debug.Log("[FloodShield VR] Connected to AI Virtual Instructor!");

                // Start receiving incoming warnings in background
                _ = ReceiveLoop();
            }
            catch (Exception ex)
            {
                Debug.LogError($"[FloodShield VR] WebSocket connection failed: {ex.Message}");
            }
        }

        void Update()
        {
            if (webSocket == null || webSocket.State != WebSocketState.Open) return;

            sendTimer += Time.deltaTime;
            if (sendTimer >= SEND_INTERVAL)
            {
                sendTimer = 0f;
                SendCurrentTelemetry();
            }
        }

        void SendCurrentTelemetry()
        {
            Vector3 pos = vrHeadset.position;

            // Detect nearest hazard in Unity scene tagged "Hazard"
            string hazardType = null;
            float hazardDist = 999f;
            GameObject[] hazards = GameObject.FindGameObjectsWithTag("Hazard");
            foreach (var h in hazards)
            {
                float d = Vector3.Distance(pos, h.transform.position);
                if (d < hazardDist)
                {
                    hazardDist = d;
                    hazardType = h.name.Contains("Elec") ? "ELECTRICAL" : "BLOCKED_ROAD";
                }
            }

            var packet = new OutgoingTelemetryPacket
            {
                pos_x = (float)Math.Round(pos.x, 2),
                pos_y = (float)Math.Round(pos.y, 2),
                pos_z = (float)Math.Round(pos.z, 2),
                tool = equippedTool,
                water_level_m = currentWaterLevel,
                water_rise_rate = waterRiseRate,
                nearest_hazard_type = hazardType,
                nearest_hazard_dist_m = hazardDist < 100f ? (float)Math.Round(hazardDist, 1) : 99f,
                victim_priority = "HIGH",
                victim_dist_m = 12.0f,
                timestamp_sec = (float)Math.Round(Time.time - drillStartTime, 1),
                zone = "Zone_A_Urban"
            };

            string json = JsonUtility.ToJson(packet);
            byte[] bytes = Encoding.UTF8.GetBytes(json);
            webSocket.SendAsync(new ArraySegment<byte>(bytes), WebSocketMessageType.Text, true, CancellationToken.None);
        }

        async Task ReceiveLoop()
        {
            var buffer = new byte[4096];
            while (webSocket.State == WebSocketState.Open)
            {
                try
                {
                    var result = await webSocket.ReceiveAsync(new ArraySegment<byte>(buffer), cts.Token);
                    if (result.MessageType == WebSocketMessageType.Close)
                    {
                        await webSocket.CloseAsync(WebSocketCloseStatus.NormalClosure, "Closing", CancellationToken.None);
                    }
                    else
                    {
                        string message = Encoding.UTF8.GetString(buffer, 0, result.Count);
                        ProcessInstructorMessage(message);
                    }
                }
                catch (Exception ex)
                {
                    Debug.LogWarning($"[FloodShield VR] Receive error: {ex.Message}");
                    break;
                }
            }
        }

        void ProcessInstructorMessage(string json)
        {
            try
            {
                IncomingInstructorResponse res = JsonUtility.FromJson<IncomingInstructorResponse>(json);
                if (res != null && res.prompts != null && res.prompts.Length > 0)
                {
                    var topPrompt = res.prompts[0];
                    DisplayHUDAlert(topPrompt);
                }
                else
                {
                    if (hudWarningPanel != null) hudWarningPanel.SetActive(false);
                }
            }
            catch (Exception ex)
            {
                Debug.LogWarning($"JSON parse error: {ex.Message}");
            }
        }

        void DisplayHUDAlert(IncomingInstructorPrompt prompt)
        {
            if (hudWarningPanel != null) hudWarningPanel.SetActive(true);
            if (hudHeadlineText != null) hudHeadlineText.text = prompt.headline;
            if (hudActionText != null) hudActionText.text = prompt.suggested_action;

            if (audioSource != null)
            {
                if (prompt.priority == "CRITICAL_WARNING" && warningSound != null)
                {
                    audioSource.PlayOneShot(warningSound);
                }
                else if (alertSound != null)
                {
                    audioSource.PlayOneShot(alertSound);
                }
            }

            Debug.Log($"[AI Virtual Instructor] {prompt.priority} ({prompt.safety_rule_code}): {prompt.headline} -> {prompt.suggested_action}");
        }

        public void EquipTool(string toolName)
        {
            equippedTool = toolName;
            Debug.Log($"[FloodShield VR] Trainee equipped tool: {toolName}");
        }

        async void OnDestroy()
        {
            if (cts != null) cts.Cancel();
            if (webSocket != null && webSocket.State == WebSocketState.Open)
            {
                await webSocket.CloseAsync(WebSocketCloseStatus.NormalClosure, "App Exiting", CancellationToken.None);
            }
        }
    }
}
