import mongoose from "mongoose";

const medicationReminderSchema = new mongoose.Schema({
    medicationName: {
        type: String,
        required: true
    },
    time: {
        type: String, 
        required: true
    },
    frequency: {
        type: String, 
        required: true
    },
    user: {
        type: mongoose.Schema.Types.ObjectId,
        ref: "User", 
        required: true
    },
    isTaken: {
        type: Boolean,
        default: false 
    }
}, { timestamps: true });

export const MedicationReminder = mongoose.model("medicationReminder", medicationReminderSchema);