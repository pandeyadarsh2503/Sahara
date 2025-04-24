import express from "express";
import { createContact, deleteContact, getAllContacts, getContactById, updateContact } from "../Controllers/contacts.controller.js";
import { authMiddleware } from "../Middlewares/authMiddleware.js";
import cors from "cors"
const app = express();
app.use(cors())

const router = express.Router();
router.use(authMiddleware);
router.post("/create", createContact);
router.get("/getContacts", getAllContacts);
router.get("/:id", getContactById);
router.put("/:id", updateContact);
router.delete("/:id", deleteContact);

export default router;