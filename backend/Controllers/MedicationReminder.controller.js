import { MedicationReminder } from "../Models/medicationReminder.model.js";
import { User } from "../Models/user.model.js";

export const createReminder = async (req, res) => {
    try {
        const { medicationName, time, frequency } = req.body;

        if (!medicationName || !time || !frequency) {
            return res.status(400).json({ message: "All fields are required." });
        }

        const newReminder = new MedicationReminder({
            medicationName,
            time,
            frequency,
            user: req.user.id 
        });

        await newReminder.save();
        res.status(201).json({ message: "Medication reminder created successfully.", reminder: newReminder });
    } catch (error) {
        res.status(500).json({ message: "Server error.", error: error.message });
    }
};

export const getAllReminders = async (req, res) => {
    console.log(req.user._id)
    try {
        if(!req.user._id){
            return res.status(404).json({
                message:"Id not found",
                success:false
            })
        }
        
        console.log(req.user._id)
        const reminders = await MedicationReminder.find({ user: req.user._id });
        
        res.status(200).json(reminders);
    }

     catch (error) {
        res.status(500).json({ message: "Server error.", error: error.message });
    }
};

export const updateReminder = async (req, res) => {
    try {
        const { id } = req.params;
        const { medicationName, time, frequency, isTaken } = req.body;
        const updatedReminder = await MedicationReminder.findOneAndUpdate(
            { _id: id, user: req.user.id }, 
            { medicationName, time, frequency, isTaken },
            { new: true, runValidators: true }
        );

        if (!updatedReminder) {
            return res.status(404).json({ message: "Reminder not found." });
        }

        res.status(200).json({ message: "Reminder updated successfully.", reminder: updatedReminder });
    } catch (error) {
        res.status(500).json({ message: "Server error.", error: error.message });
    }
};

export const deleteReminder = async (req, res) => {
    try {
        const { id } = req.params;

        const deletedReminder = await MedicationReminder.findOneAndDelete({ _id: id, user: req.user.id });

        if (!deletedReminder) {
            return res.status(404).json({ message: "Reminder not found." });
        }

        res.status(200).json({ message: "Reminder deleted successfully." });
    } catch (error) {
        res.status(500).json({ message: "Server error.", error: error.message });
    }
};