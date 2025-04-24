// import { bool, boolean } from "joi";
import mongoose from "mongoose";

const contactSchema = new mongoose.Schema({
    contactName: {
        type: String,
        required: true
    },
    phoneNumber: {
        type: String,
        required: true,
        unique: true
    },
    relationship: {
        type: String,
        required: true
    },
    primary:{
        type:Boolean,
        default:false
    },
    user: {
        type: mongoose.Schema.Types.ObjectId,
        ref: "User", 
        required: true
    }
}, { timestamps: true });

export const contactDetails = mongoose.model("contacts", contactSchema);