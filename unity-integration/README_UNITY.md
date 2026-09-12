# Unity VR Integration Guide for FloodShield AI

This folder contains ready-to-use C# scripts for integrating your **Unity VR Project** (Meta Quest / SteamVR / OpenXR / Vive) with the **FloodShield AI Backend**.

---

## 📦 What's Inside

1. **`VRTelemetryClient.cs`**:
   - Manages live bi-directional WebSocket connection (`ws://localhost:8000/ws/vr-telemetry`).
   - Streams trainee position ($x, y, z$), equipped tool, and hazard proximity at ~6.6 Hz.
   - Receives tactical safety warnings and audio cues from the deterministic **AI Virtual Instructor** and triggers your VR helmet HUD.

2. **`VRSessionManager.cs`**:
   - Logs drill events (`VICTIM_TRIAGE`, `VICTIM_RESCUE`, `TOOL_EQUIP`, `HAZARD_EXPOSURE`).
   - Submits telemetry to `POST /api/v1/vr/telemetry-evaluate` at the end of the drill.
   - Receives and displays the **8-Vector Competency Scores** and qualification tier on a VR scoreboard.

3. **`VRSafeRouteRenderer.cs`**:
   - Calls `POST /api/v1/routing/safe-route` (A* or Dijkstra).
   - Draws a glowing 3D safe evacuation path on the VR terrain using Unity's `LineRenderer`.

---

## 🛠️ Step-by-Step Setup in Unity

### 1. Copy Scripts into Unity
Copy the `.cs` files from `c:\ai_vr\unity-integration\` into your Unity project under:
`Assets/Scripts/FloodShield/`

### 2. Create the Manager GameObject
1. In your Unity Scene hierarchy, create an empty GameObject named `[FloodShield_Manager]`.
2. Attach the three scripts:
   - `VRTelemetryClient`
   - `VRSessionManager`
   - `VRSafeRouteRenderer`

### 3. Assign References in Inspector
- **VR Headset Transform**: Drag your `CenterEyeAnchor` (or `Main Camera`) into the `vrHeadset` slot on `VRTelemetryClient`.
- **HUD Elements**: (Optional) Assign a World-Space Canvas UI Text element for `hudHeadlineText` and `hudActionText`.
- **AudioSource**: Assign an `AudioSource` and warning `.wav` / `.mp3` clip for audio cues.

### 4. Tag Hazards in your Scene
Ensure any hazard GameObjects in your Unity scene (like submerged transformers or road washouts) have the tag:
- Tag: `Hazard`
- Name them descriptively (e.g. `Hazard_Electrical_11kV` or `Hazard_BlockedRoad`).

### 5. Hook up Victim Rescues
When a trainee touches or triages a victim in Unity, call:
```csharp
FindObjectOfType<VRSessionManager>().OnVictimRescued("Victim Child", transform.position);
```

When trainee reaches the final elevated shelter, call:
```csharp
FindObjectOfType<VRSessionManager>().EndDrillAndEvaluate();
```

---

## 🌐 Network Configuration (Local vs Meta Quest Standalone)

- **PC VR (Oculus Link / AirLink / SteamVR):**
  - Use `ws://localhost:8000/ws/vr-telemetry` and `http://localhost:8000/api/v1/...`
- **Standalone Meta Quest (Installed APK on headset over Wi-Fi):**
  - Find your PC's Wi-Fi IP address (e.g., `192.168.1.50`).
  - Set the URLs to:
    - `ws://192.168.1.50:8000/ws/vr-telemetry`
    - `http://192.168.1.50:8000/api/v1/vr/telemetry-evaluate`
    - `http://192.168.1.50:8000/api/v1/routing/safe-route`
  - Ensure your Windows Firewall allows inbound connections on port 8000.
