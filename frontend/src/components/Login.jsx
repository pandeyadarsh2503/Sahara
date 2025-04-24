import React, { use, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import Navbar from "./Navbar";
import { setUser } from "../redux/userslice";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import axios from "axios"; // Ensure axios is imported
import { setLoading } from "@/redux/authSlice";
import { Button } from "./ui/button";
import { Loader2 } from "lucide-react";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(""); // Added error state
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const {loading} = useSelector(store=>store.auth)


  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
        dispatch(setLoading(true));
      const res = await axios.post(`http://localhost:8000/api/v1/user/login`, {
        email,
        password,
      });
      if (res.data.success) {
        console.log("User logged in successfully");
        localStorage.setItem("token",res.data.token)
        dispatch(setUser(res.data.user.fullname));
        toast.success("Login successful!");
        navigate("/home");
      }
    } catch (error) {
      console.error("Login failed:", error.response?.data?.message || error.message);
      setError(error.response?.data?.message || "Login failed. Please try again.");
    }finally{
        dispatch(setLoading(false));
    }
  };

  return (
    <div>
      <Navbar />
      <div className="flex items-center justify-center min-h-screen bg-[#f8faff] px-4">
        <div className="bg-white rounded-xl shadow-lg p-8 w-full max-w-md">
          <h2 className="text-2xl font-bold text-center mb-6 text-[#2f247d]">
            Welcome Back to Sahara
          </h2>
          {error && (
            <p className="text-red-500 text-center mb-4">{error}</p>
          )}
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Email
              </label>
              <input
                type="email"
                name="email"
                value={email} // Fixed to use email state
                onChange={(e) => setEmail(e.target.value)} // Fixed handler
                required
                className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-[#2f247d]"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Password
              </label>
              <input
                type="password"
                name="password"
                value={password} // Fixed to use password state
                onChange={(e) => setPassword(e.target.value)} // Fixed handler
                required
                className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-[#2f247d]"
              />
            </div>

            {/* <button
              type="submit"
              className="w-full bg-[#2f247d] text-white py-2 rounded-lg hover:bg-[#4437a0] transition"
            >
              Login
            </button> */}
             <div className="flex items-center justify-between">
            {
              loading?<Button className='w-full bg-[#2f247d] text-white font-bold py-2 px-4 rounded h-10 flex items-center justify-center gap-2'> <Loader2 className='text-center   animate-spin'/> Please wait</Button> : <button
            
              type="submit"
              className="w-full bg-[#2f247d]  text-white font-bold py-2 px-4 rounded group relative h-10  overflow-hidden  text-md  border-gold  text-center"
            >
              Login
              <div className="absolute inset-0 h-full w-full scale-0 rounded-2xl transition-all duration-300 group-hover:scale-100 group-hover:bg-white/30"></div>
            </button>
            }
           
          </div>
          </form>

          <p className="text-center text-sm text-gray-600 mt-4">
            Don’t have an account?{" "}
            <span
              onClick={() => navigate("/signup")}
              className="text-[#2f247d] font-medium cursor-pointer"
            >
              Sign Up
            </span>
          </p>
        </div>
      </div>
    </div>
  );
}