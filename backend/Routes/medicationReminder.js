import express from "express";
import {
    createReminder,
    getAllReminders,
    updateReminder,
    deleteReminder
} from "../Controllers/MedicationReminder.controller.js";
import { authMiddleware } from "../Middlewares/authMiddleware.js";

const router = express.Router();

router.use(authMiddleware);
router.post("/createReminder", createReminder);
router.get("/getReminders",getAllReminders);
router.put("/:id", updateReminder);
router.delete("/:id", deleteReminder);

export default router;