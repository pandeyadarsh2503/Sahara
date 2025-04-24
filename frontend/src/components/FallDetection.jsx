import { useState, useEffect } from "react";
import axios from "axios";

export default function FallDetection() {
  const [status, setStatus] = useState("Initializing...");
  const [videoStarted, setVideoStarted] = useState(false);

  const startCamera = () => {
    setVideoStarted(true);
  };

  useEffect(() => {
    if (!videoStarted) return;

    const interval = setInterval(async () => {
      try {
        const response = await axios.get("http://localhost:5000/fall_status");
        const { fall_confirmed, fall_detected } = response.data;

        if (fall_confirmed) {
          setStatus("🔴 FALL CONFIRMED");
        } else if (fall_detected) {
          setStatus("🟡 FALL DETECTED");
        } else {
          setStatus("🟢 NORMAL");
        }
      } catch (error) {
        console.error("Error fetching fall status:", error);
        setStatus("❌ Error connecting to backend");
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [videoStarted]);

  return (
    <div className="p-6 max-w-xl mx-auto text-center">
      <h1 className="text-3xl font-bold mb-4">Fall Detection System</h1>

      {!videoStarted ? (
        <button
          onClick={startCamera}
          className="bg-blue-600 text-white px-6 py-3 rounded-xl shadow-md hover:bg-blue-700 transition"
        >
          Start Camera
        </button>
      ) : (
        <>
          <div className="mt-6">
            <img
              src="http://localhost:5000/video_feed"
              alt="Live Camera Feed"
              className="rounded-lg shadow-lg border-2 border-gray-300"
              style={{ width: "600px", height: "480px", borderRadius: "12px" }}
            />
          </div>

          <p className="mt-4 text-xl font-semibold">{status}</p>
        </>
      )}
    </div>
  );
}
