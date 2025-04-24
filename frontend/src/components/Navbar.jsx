import { getToken } from "@/lib/token";
import { setUser } from "@/redux/userSlice";
import axios from "axios";
import { useDispatch, useSelector } from "react-redux";
import { Link, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import logo from "../assets/logo.png";
import { Avatar, AvatarFallback, AvatarImage } from "./ui/avatar";
import { Button } from "./ui/button";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "./ui/popover";

const Navbar = () => {
  const navigate = useNavigate();
  const { user } = useSelector((store) => store.user);
  const token = getToken();
  const dispatch = useDispatch();

  const logoutHandler = async () => {
    try {
      const res = await axios.post("http://localhost:8000/api/v1/user/logout", {
        Headers: {
          Authorization: token,
        },
      });
      if (res.data.success) {
        dispatch(setUser(null));
        navigate("/");
        toast.success(res.data.message);
      }
    } catch (error) {
      console.log(error);
    }
  };

  return (
    <header className="flex items-center justify-between px-6 py-4 bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500 text-white shadow-lg z-50">
      <div className="flex items-center gap-3">
        <img src={logo} alt="Logo" className="h-10 w-10 rounded-full border-2 border-white" />
        <span className="text-xl font-bold tracking-wide">Sahara</span>
      </div>
      <nav className="hidden md:flex gap-8 text-sm font-medium">
        <div onClick={() => navigate("/")} className="hover:text-yellow-300 transition cursor-pointer">
          Home
        </div>
        <div className="hover:text-yellow-300 transition cursor-pointer">Features</div>
        <div className="hover:text-yellow-300 transition cursor-pointer">About</div>
        <div className="hover:text-yellow-300 transition cursor-pointer">Contact</div>
      </nav>

      {user ? (
        <Popover>
          <PopoverTrigger asChild>
            <Avatar className="cursor-pointer">
              <AvatarImage src={user?.profile?.profilePhoto} alt="User Avatar" />
              <AvatarFallback>AD</AvatarFallback>
            </Avatar>
          </PopoverTrigger>
          <PopoverContent className="w-80 p-4 bg-white text-black shadow-md rounded-xl border border-gray-200">
            <div className="flex gap-4 items-center">
              <Avatar>
                <AvatarImage src={user?.profile?.profilePhoto} />
                <AvatarFallback>JD</AvatarFallback>
              </Avatar>
              <div>
                <h3 className="font-semibold text-lg">{user}</h3>
                <Button onClick={logoutHandler} variant="link" className="text-red-500 mt-1">
                  Logout
                </Button>
              </div>
            </div>
          </PopoverContent>
        </Popover>
      ) : (
        <div className="gap-4 flex">
          <Link to="/login">
            <Button className="bg-white text-purple-600 hover:bg-purple-100 font-semibold px-5 rounded-full">
              Login
            </Button>
          </Link>
          <Link to="/signup">
            <Button className="bg-white text-purple-600 font-semibold px-5 rounded-full">
              SignUp
            </Button>
          </Link>
        </div>
      )}
    </header>
  );
};

export default Navbar;
