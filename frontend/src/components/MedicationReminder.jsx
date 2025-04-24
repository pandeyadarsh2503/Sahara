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
import {
  Clock,
  Plus,
  Check,
  X,
  Bell,
  Calendar,
  Mic,
  VolumeIcon as VolumeUp,
} from "lucide-react";
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { getToken } from "@/lib/token";
import { href } from "react-router-dom";

export default function MedicationReminder() {
  const [medications, setMedications] = useState([]);
  const [newMedication, setNewMedication] = useState({
    medicationName: "",
    time: "",
    frequency: "Daily",
  });
  const [input,setInput] = useState("")
  const [dialogOpen, setDialogOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const token = getToken();
  const submithandler = () => {
    window.location.href = "http://localhost:8020/";
  }
  // Fetch all reminders from the backend
  const fetchMedications = async () => {
    try {
      
      setLoading(true);
      const res = await axios.get("http://localhost:8000/api/v1/user/medic/getReminders", {
        headers:{Authorization:token}
      });
      console.log(res);
      setMedications(res.data);
    } catch (error) {
      console.error("Failed to fetch reminders:", error);
      // toast.error("Failed to load reminders. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  // Add a new medication reminder
  const handleAddMedication = async () => {
    if (!newMedication.medicationName || !newMedication.time) {
      toast.error("Please fill in all required fields.");
      return;
    }

    try {
      setLoading(true);
      
      const res = await axios.post(
        "http://localhost:8000/api/v1/user/medic/createReminder",
        newMedication,
        {headers:{Authorization:token}}
      );

      if (res.data.success) {
        setMedications([...medications, res.data.reminder]);
        setNewMedication({ medicationName: "", time: "", frequency: "Daily" });
        setDialogOpen(false);
        toast.success("Medication reminder added successfully!");
      }
    } catch (error) {
      console.error("Failed to add reminder:", error);
      toast.error("Failed to add reminder. Please try again.");
    } finally {
      setLoading(false);
      fetchMedications();
      setDialogOpen(false)
    }
  };

  // Toggle medication status (mark as taken/untaken)
  const toggleMedicationStatus = async (id, isTaken) => {
    try {
      setLoading(true);
      const res = await axios.put(
        `http://localhost:8000/api/v1/user/medic/${id}`,
        { isTaken: !isTaken },
        { headers:{Authorization:token} }
      );

      if (res.data.success) {
        setMedications(
          medications.map((med) =>
            med._id === id ? { ...med, isTaken: !isTaken } : med
          )
        );
        toast.success(
          `${res.data.reminder.medicationName} has been ${
            isTaken ? "unmarked" : "marked as taken"
          }.`
        );
      }
    } catch (error) {
      console.error("Failed to update reminder:", error);
      // toast.error("Failed to update reminder. Please try again.");
    } finally {
      setLoading(false);
      fetchMedications();
    }
  };

  // Delete a medication reminder
  const handleDeleteMedication = async (id) => {
    try {
      setLoading(true);
      const res = await axios.delete(
        `http://localhost:8000/api/v1/user/medic/${id}`,
        {headers:{Authorization:token} }
      );

      if (res.data.success) {
        setMedications(medications.filter((med) => med._id !== id));
        toast.success("Medication reminder deleted successfully!");
      }
    } catch (error) {
      console.error("Failed to delete reminder:", error);
      // toast.error("Failed to delete reminder. Please try again.");
    } finally {
      setLoading(false);
      fetchMedications();
    }
  };

  // Fetch reminders on component mount
  useEffect(() => {
    fetchMedications();
  }, []);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Bell className="h-5 w-5 text-orange-500" />
          Medication Reminders
        </CardTitle>
        <CardDescription>
          Keep track of your daily medications and when to take them
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {loading ? (
            <p className="text-center text-gray-500">Loading reminders...</p>
          ) : medications?.length > 0 ? (
            medications.map((medication) => (
              <div
                key={medication._id}
                className={`flex items-center justify-between p-3 rounded-lg border ${
                  medication.isTaken
                    ? "bg-green-50 border-green-200"
                    : "bg-white border-gray-200"
                }`}
              >
                <div className="flex items-center gap-3">
                  <Button
                    variant={medication.isTaken ? "default" : "outline"}
                    size="icon"
                    className={`h-8 w-8 rounded-full ${
                      medication.isTaken
                        ? "bg-green-500 hover:bg-green-600"
                        : ""
                    }`}
                    onClick={() =>
                      toggleMedicationStatus(medication._id, medication.isTaken)
                    }
                  >
                    {medication.isTaken ? (
                      <Check className="h-4 w-4" />
                    ) : (
                      <X className="h-4 w-4" />
                    )}
                  </Button>
                  <div>
                    <p
                      className={`font-medium ${
                        medication.isTaken
                          ? "line-through text-gray-500"
                          : ""
                      }`}
                    >
                      {medication.medicationName}
                    </p>
                    <div className="flex items-center gap-2 text-sm text-gray-500">
                      <Clock className="h-3 w-3" />
                      <span>{medication.time}</span>
                      <span>•</span>
                      <Calendar className="h-3 w-3" />
                      <span>{medication.frequency}</span>
                    </div>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleDeleteMedication(medication._id)}
                >
                  Delete
                </Button>
              </div>
            ))
          ) : (
            <div className="text-center py-8 text-gray-500">
              <p>No medication reminders added yet</p>
            </div>
          )}
        </div>
      </CardContent>
      <CardFooter className="border-t bg-gray-50/50 p-4">
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button className="w-[50%] gap-2">
              <Plus className="h-4 w-4" />
              Add Medication Reminder
            </Button>

            
          </DialogTrigger>
          <Button onClick={submithandler} className="w-[50%]  border-2 border-black ">
              <Plus className="h-4 w-4 border-2 border-black  " />
              Add prescription
            </Button>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Add New Medication</DialogTitle>
              <DialogDescription>
                Add details about your medication and when you need to take it.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="medication-name">Medication Name</Label>
                <Input
                  id="medication-name"
                  placeholder="Enter medication name"
                  value={newMedication.medicationName}
                  onChange={(e) =>
                    setNewMedication({
                      ...newMedication,
                      medicationName: e.target.value,
                    })
                  }
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="medication-time">Time to Take</Label>
                <Input
                  id="medication-time"
                  type="time"
                  value={newMedication.time}
                  onChange={(e) =>
                    setNewMedication({ ...newMedication, time: e.target.value })
                  }
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="medication-frequency">Frequency</Label>
                <Select
                  value={newMedication.frequency}
                  onValueChange={(value) =>
                    setNewMedication({ ...newMedication, frequency: value })
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select frequency" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Daily">Daily</SelectItem>
                    <SelectItem value="Weekly">Weekly</SelectItem>
                    <SelectItem value="As needed">As needed</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setDialogOpen(false)}>
                Cancel
              </Button>
              <Button onClick={handleAddMedication}>Add Reminder</Button>
              <Button>Add reminder prescription</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </CardFooter>
    </Card>
  );
}