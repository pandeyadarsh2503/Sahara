"use client";

import { useState, useEffect } from "react";
import axios from "axios";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Phone, Plus, Heart, PhoneCall } from "lucide-react";
import { toast } from "../components/hooks/useToast";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { getToken } from "@/lib/token";

export default function EmergencyContacts() {
  const [contacts, setContacts] = useState([]);
  const [newContact, setNewContact] = useState({ contactName: "", phoneNumber: "", relationship: "", primary: false });
  const [dialogOpen, setDialogOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const token = getToken()

  const fetchContacts = async () => {
    try {
      setLoading(true);
      
      const res = await axios.get("http://localhost:8000/api/v1/user/contact/getContacts", { headers:{Authorization:token} });
      setContacts(res.data);
      console.log(res.data)
    } catch (error) {
      console.error("Failed to fetch contacts:", error.response?.data || error.message);
    //   toast.error("Failed to load contacts. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleAddContact = async () => {
    if (!newContact.contactName || !newContact.phoneNumber) {
    //   toast.error("Please fill in all required fields.");
      return;
    }

    try {
      setLoading(true);
      const res = await axios.post(
        "http://localhost:8000/api/v1/user/contact/create",
        newContact,
        {headers:{Authorization:token}}
      );

      if (res.data.success) {
        setContacts([...contacts, res.data.contact]);
        setNewContact({ contactName: "", phoneNumber: "", relationship: "", primary: false });
        setDialogOpen(false);
        toast.success("Contact added successfully!");
        
      }
    } catch (error) {
      console.error("Failed to add contact:", error.response?.data || error.message);
    } finally {
      setLoading(false);
      fetchContacts();
      setDialogOpen(false);
    }
  };

  const handleEmergencyCall = (contact) => {
    toast({
      title: `Calling ${contact.contactName}`,
      description: `Dialing ${contact.phoneNumber}...`,
      variant: "default",
    });
  };

  useEffect(() => {
    fetchContacts();
  }, []);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Phone className="h-5 w-5 text-red-500" />
          Emergency Contacts
        </CardTitle>
        <CardDescription>People to contact in case of emergency</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {loading ? (
            <p className="text-center text-gray-500">Loading contacts...</p>
          ) : contacts?.length > 0 ? (
            contacts.map((contact) => (
              <div
                key={contact._id}
                className={`flex items-center justify-between p-3 rounded-lg border ${
                  contact.primary ? "bg-red-50 border-red-200" : "bg-white border-gray-200"
                }`}
              >
                <div className="flex items-center gap-3">
                  <Avatar className={contact.primary ? "border-2 border-red-500" : ""}>
                    <AvatarFallback>{contact.contactName.charAt(0)}</AvatarFallback>
                  </Avatar>
                  <div>
                    <p className="font-medium flex items-center gap-1">
                      {contact.contactName}
                      {contact.primary && <Heart className="h-3 w-3 text-red-500 fill-red-500" />}
                    </p>
                    <div className="flex items-center gap-2 text-sm text-gray-500">
                      <Phone className="h-3 w-3" />
                      <span>{contact.phoneNumber}</span>
                      <span>•</span>
                      <span>{contact.relationship}</span>
                    </div>
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    className="text-green-600 border-green-200"
                    onClick={() => handleEmergencyCall(contact)}
                  >
                    <PhoneCall className="h-4 w-4 mr-1" />
                    Call
                  </Button>
                </div>
              </div>
            ))
          ) : (
            <div className="text-center py-8 text-gray-500">
              <p>No emergency contacts added yet</p>
            </div>
          )}
        </div>
      </CardContent>
      <CardFooter className="border-t bg-gray-50/50 p-4">
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button className="w-full gap-2">
              <Plus className="h-4 w-4" />
              Add Emergency Contact
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Add Emergency Contact</DialogTitle>
              <DialogDescription>Add someone who should be contacted in case of emergency.</DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="contact-name">Contact Name</Label>
                <Input
                  id="contact-name"
                  placeholder="Enter name"
                  value={newContact.contactName}
                  onChange={(e) => setNewContact({ ...newContact, contactName: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="contact-phone">Phone Number</Label>
                <Input
                  id="contact-phone"
                  placeholder="Enter phone number"
                  value={newContact.phoneNumber}
                  onChange={(e) => setNewContact({ ...newContact, phoneNumber: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="contact-relationship">Relationship</Label>
                <Input
                  id="contact-relationship"
                  placeholder="Family, Doctor, Neighbor, etc."
                  value={newContact.relationship}
                  onChange={(e) => setNewContact({ ...newContact, relationship: e.target.value })}
                />
              </div>
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="primary-contact"
                  checked={newContact.primary}
                  onChange={(e) => setNewContact({ ...newContact, primary: e.target.checked })}
                  className="rounded border-gray-300"
                />
                <Label htmlFor="primary-contact">Set as primary emergency contact</Label>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setDialogOpen(false)}>
                Cancel
              </Button>
              <Button onClick={handleAddContact} disabled={loading}>
                {loading ? "Adding..." : "Add Contact"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </CardFooter>
    </Card>
  );
}