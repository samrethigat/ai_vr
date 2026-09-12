using System;
using System.Collections;
using System.Text;
using UnityEngine;
using UnityEngine.Networking;

namespace FloodShield.VR
{
    /// <summary>
    /// Fetches the dynamic hazard-avoiding safe route from the FastAPI A* Route Engine
    /// and renders a 3D glowing path / breadcrumb trail directly on the VR terrain.
    /// </summary>
    [RequireComponent(typeof(LineRenderer))]
    public class VRSafeRouteRenderer : MonoBehaviour
    {
        [Header("Route API Endpoint")]
        public string routingUrl = "http://localhost:8000/api/v1/routing/safe-route";

        [Header("Route Settings")]
        public float originLatitude = 26.1722f;
        public float originLongitude = 91.7458f;
        public string algorithm = "A_STAR"; // "A_STAR" or "DIJKSTRA"
        
        [Header("World Scaling")]
        [Tooltip("Conversion scale from geographic coordinates delta to Unity world space meters")]
        public float geoScaleMultiplier = 10000f;
        public float pathHeightOffset = 0.15f; // Raised slightly above ground to prevent z-fighting

        private LineRenderer lineRenderer;

        [Serializable]
        public class RouteRequestDTO
        {
            public float origin_latitude;
            public float origin_longitude;
            public string algorithm;
            public float hazard_penalty_weight = 5.0f;
            public float flood_risk_weight = 4.0f;
        }

        [Serializable]
        public class WaypointDTO
        {
            public float latitude;
            public float longitude;
            public float elevation_m;
            public float water_level_m;
        }

        [Serializable]
        public class RouteSegmentDTO
        {
            public float distance_km;
            public float estimated_time_min;
            public float safety_score;
            public WaypointDTO[] waypoints;
            public string[] turn_by_turn_instructions;
        }

        [Serializable]
        public class SafeRouteResponseDTO
        {
            public RouteSegmentDTO primary_safest_route;
            public RouteSegmentDTO alternative_route;
            public string destination_shelter_name;
        }

        void Awake()
        {
            lineRenderer = GetComponent<LineRenderer>();
            ConfigureLineVisuals();
        }

        void Start()
        {
            FetchAndDrawSafeRoute();
        }

        void ConfigureLineVisuals()
        {
            lineRenderer.startWidth = 0.4f;
            lineRenderer.endWidth = 0.4f;
            lineRenderer.useWorldSpace = true;
            lineRenderer.startColor = new Color(0.06f, 0.72f, 0.5f, 0.9f); // Emerald green
            lineRenderer.endColor = new Color(0.2f, 0.9f, 0.6f, 0.9f);
        }

        public void FetchAndDrawSafeRoute()
        {
            StartCoroutine(FetchRouteCoroutine());
        }

        private IEnumerator FetchRouteCoroutine()
        {
            var reqBody = new RouteRequestDTO
            {
                origin_latitude = originLatitude,
                origin_longitude = originLongitude,
                algorithm = algorithm
            };

            string json = JsonUtility.ToJson(reqBody);
            byte[] bodyRaw = Encoding.UTF8.GetBytes(json);

            UnityWebRequest req = new UnityWebRequest(routingUrl, "POST");
            req.uploadHandler = new UploadHandlerRaw(bodyRaw);
            req.downloadHandler = new DownloadHandlerBuffer();
            req.SetRequestHeader("Content-Type", "application/json");

            yield return req.SendWebRequest();

            if (req.result == UnityWebRequest.Result.Success)
            {
                SafeRouteResponseDTO res = JsonUtility.FromJson<SafeRouteResponseDTO>(req.downloadHandler.text);
                if (res != null && res.primary_safest_route != null && res.primary_safest_route.waypoints != null)
                {
                    RenderRouteIn3D(res.primary_safest_route.waypoints);
                    Debug.Log($"[FloodShield VR] Safe route drawn! Shelter: {res.destination_shelter_name} | Safety: {res.primary_safest_route.safety_score}%");
                }
            }
            else
            {
                Debug.LogWarning($"Failed to fetch route: {req.error}");
            }
        }

        private void RenderRouteIn3D(WaypointDTO[] waypoints)
        {
            lineRenderer.positionCount = waypoints.Length;

            for (int i = 0; i < waypoints.Length; i++)
            {
                float dx = (waypoints[i].longitude - originLongitude) * geoScaleMultiplier;
                float dz = (waypoints[i].latitude - originLatitude) * geoScaleMultiplier;
                float y = pathHeightOffset;

                // Adjust to local terrain height if a raycast hits ground
                RaycastHit hit;
                if (Physics.Raycast(new Vector3(dx, 50f, dz), Vector3.down, out hit, 100f))
                {
                    y = hit.point.y + pathHeightOffset;
                }

                lineRenderer.SetPosition(i, new Vector3(dx, y, dz));
            }
        }
    }
}
