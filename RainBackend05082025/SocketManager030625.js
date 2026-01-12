
// SocketManager030625.js (patched for RAIN v2025 integration)

const io = require("socket.io-client");
const axios = require("axios");
const db = require("../utils/db");
const { validateLicenseToken } = require("../utils/licenseValidator");

const flaskSocket = io("ws://127.0.0.1:5000");
const userSessions = new Map();

module.exports = function (socket, ioInstance) {
  global.activeUsers = global.activeUsers || new Map();

  socket.on("GenerateMatches", async ({ userId, sessionId }) => {
    if (!(await validateLicenseToken(userId))) {
      socket.emit("system_message", { userId, text: "❌ Your RAIN license has expired." });
      return;
    }

    userSessions.set(userId, sessionId);

    flaskSocket.emit("matchmaking_request", {
      session_id: sessionId,
      user_id: userId,
    });
  });

  socket.on("SendMessageToBot", async (message) => {
    const userId = message.userId;
    const sessionId = userSessions.get(userId) || message.sessionId || "default_session";

    if (!(await validateLicenseToken(userId))) {
      socket.emit("system_message", { userId, text: "❌ Your RAIN license has expired." });
      return;
    }

    flaskSocket.emit("chat_request", {
      user_id: userId,
      message: message.text,
      session_id: sessionId,
    });
  });

  flaskSocket.on("chat_response", async (data) => {
    const { user_id, reply } = data;
    socket.emit("RAIN_response", { userId: user_id, text: reply });

    // Log chat behavior
    await db.save("RAINEvents", {
      userId: user_id,
      sessionId: userSessions.get(user_id),
      event: "chat_response",
      data: { reply },
      timestamp: new Date(),
    });
  });

  flaskSocket.on("matchmaking_response", async (data) => {
    const { session_id, match_count } = data;
    socket.emit("RAIN_response", {
      userId: data.user_id,
      text: `✅ ${match_count} connections generated for session ${session_id}.`,
    });

    await db.save("RAINEvents", {
      userId: data.user_id,
      sessionId: session_id,
      event: "matchmaking_complete",
      data,
      timestamp: new Date(),
    });
  });
};
