import { contactDetails } from "../Models/contact.models.js";
import { User } from "../Models/user.model.js";

export const createContact = async (req, res) => {
    try {
        const { contactName, phoneNumber, relationship,primary } = req.body;

        // Validate required fields
        if (!contactName || !phoneNumber || !relationship) {
            return res.status(400).json({ message: "All fields are required." });
        }
        
        // Create a new contact associated with the logged-in user
        const newContact = new contactDetails({
            contactName,
            phoneNumber,
            relationship,
            primary,
            user: req.user.id // Assuming `req.user.id` contains the logged-in user's ID
        });

        await newContact.save();

        // Add the contact to the user's contacts array
        await User.findByIdAndUpdate(req.user.id, {
            $push: { contacts: newContact._id }
        });

        res.status(201).json({ message: "Contact created successfully.", contact: newContact });
    } catch (error) {
        if (error.code === 11000) {
            return res.status(400).json({ message: "Phone number must be unique." });
        }
        res.status(500).json({ message: "Server error.", error: error.message });
    }
};

export const getAllContacts = async (req, res) => {
    try {

        const contacts = await contactDetails.find({ user: req.user.id });
        res.status(200).json(contacts);
    } catch (error) {
        res.status(500).json({ message: "Server error.", error: error.message });
    }
};

export const getContactById = async (req, res) => {
    try {
        const { id } = req.params;

        // Fetch the contact by ID and ensure it belongs to the logged-in user
        const contact = await contactDetails.findOne({ _id: id, user: req.user.id });

        if (!contact) {
            return res.status(404).json({ message: "Contact not found." });
        }

        res.status(200).json(contact);
    } catch (error) {
        res.status(500).json({ message: "Server error.", error: error.message });
    }
};

export const updateContact = async (req, res) => {
    try {
        const { id } = req.params;
        const { contactName, phoneNumber, relationship,primary } = req.body;

        // Update the contact only if it belongs to the logged-in user
        const updatedContact = await contactDetails.findOneAndUpdate(
            { _id: id, user: req.user.id },
            { contactName, phoneNumber, relationship },
            { new: true, runValidators: true }
        );

        if (!updatedContact) {
            return res.status(404).json({ message: "Contact not found." });
        }

        res.status(200).json({ message: "Contact updated successfully.", contact: updatedContact });
    } catch (error) {
        if (error.code === 11000) {
            return res.status(400).json({ message: "Phone number must be unique." });
        }
        res.status(500).json({ message: "Server error.", error: error.message });
    }
};

export const deleteContact = async (req, res) => {
    try {
        const { id } = req.params;

        // Delete the contact only if it belongs to the logged-in user
        const deletedContact = await contactDetails.findOneAndDelete({ _id: id, user: req.user.id });

        if (!deletedContact) {
            return res.status(404).json({ message: "Contact not found." });
        }

        // Remove the contact from the user's contacts array
        await User.findByIdAndUpdate(req.user.id, {
            $pull: { contacts: id }
        });

        res.status(200).json({ message: "Contact deleted successfully." });
    } catch (error) {
        res.status(500).json({ message: "Server error.", error: error.message });
    }
};