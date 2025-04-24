import { login, logout, register } from "../Controllers/user.controller.js";
import express from "express"
import { signupValidation } from "../Middlewares/authValidation.js";
const router = express.Router();

router.route("/register").post(signupValidation,register);
router.route("/login").post(login);
router.route("/logout").post(logout);
export default router;
