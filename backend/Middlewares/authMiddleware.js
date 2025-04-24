import jwt from "jsonwebtoken";
import { User } from "../Models/user.model.js";

export const authMiddleware = async (req, res, next) => {
  try {
    // console.log("🧁 Incoming Cookies:", req.cookies);

    const token =  req.headers.authorization;
    if (!token) {
      return res.status(401).json({ message: "No token provided, authorization denied." });
    }

    console.log("🔐 Token used for auth:", token);

    const decoded = jwt.verify(token, process.env.SECRET_KEY);
    const user = await User.findById(decoded.userId).select("-password");

    if (!user) {
      return res.status(401).json({ message: "User not found, authorization denied." });
    }

    req.user = user;
    console.log(req.user)
    next();
  } catch (error) {
    return res.status(401).json({
      message: "Invalid token, authorization denied.",
      error: error.message,
    });
  }
};
