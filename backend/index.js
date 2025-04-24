import express from "express"
import cookieParser from "cookie-parser";
import cors from "cors";
import dotenv from "dotenv";
import  connectDB  from "./utils/db.js";
import userRouter from "./Routes/user.route.js"
import contactRouter from "./Routes/contacts.js"
import  MedicationReminder  from "./Routes/medicationReminder.js";
dotenv.config({});
const app = express();
app.use(express.json())
app.use(cookieParser());
app.use(cors({
    origin:["*","http://localhost:5173"],
    methods:["PUT","POST","GET","DELETE"]
}));
const PORT = process.env.PORT || 3000;
app.use("/api/v1/user", userRouter);
app.use("/api/v1/user/contact",contactRouter );
app.use("/api/v1/user/medic",MedicationReminder );

app.listen(PORT, ()=>{
    connectDB();
    console.log("server is running on the port" ,PORT)
})
