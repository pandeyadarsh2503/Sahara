import mongoose, { Schema } from "mongoose";

const userSchema = mongoose.Schema({
    fullname :{
        type:String,
        required:true
    },
    email:{
        type:String,
        required:true,
        unique:true
    },
    password:{
        type:String,
        required:true
    },
    contacts: [
        {
            type: mongoose.Schema.Types.ObjectId,
            ref: "contacts" 
        }
    ]
},{timestamps:true});

export const User = mongoose.model("user",userSchema);