import { User } from "../Models/user.model.js";
import bcrypt from "bcryptjs";
import jwt from "jsonwebtoken";
import cookieParser from "cookie-parser";

export const register = async (req, res) => {
  try {
    const { fullname, email, password } = req.body;
    if (!fullname || !email || !password) {
      return res.status(400).json({
        message: "something is missing",
        success: false,
      });
    }
    const user = await User.findOne({ email });
    if (user) {
      return res.status(400).json({
        message: "email already exist",
        success: false,
      });
    }
    const hashedPassword = await bcrypt.hash(password, 10);

    await User.create({
      fullname,
      email,
      password: hashedPassword,
    });

    return res.status(200).json({
      message: "User created successfully",
      success: true,
    });
  } catch (error) {
    console.log(error);
  }
};

export const login = async (req, res) => {
  try {
    const { email, password } = req.body;
    if (!email || !password) {
      return res.status(400).json({
        message: "something is missing",
        success: false,
      });
    }
    let user = await User.findOne({ email });
    if (!user) {
      return res.status(400).json({
        message: "Invalid email or password",
        success: false,
      });
    }
    const ispassEqual = bcrypt.compare(password, user.password);
    if (!ispassEqual) {
      return res.status(403).json({
        message: "Invalid email or password",
      });
    }
    const tokenData = {
      userId: user._id,
    };
    const token = jwt.sign(tokenData, process.env.SECRET_KEY, {
      expiresIn: "1d",
    });
    user = {
        _id: user._id,
        fullname: user.fullname,
        email: user.email,
        
      }
      return res.status(200).json({
        message:`Welcome back ${user.fullname}`,
        user,
        success:true,
        token
      })
  } catch (error) {
    console.log(error);
  }
};
export const logout = async (req, res) => {
  try {
    // Clear the JWT token cookie
    res.cookie('token', '', {
      httpOnly: true,
      expires: new Date(0), // Set expiration to past date to immediately expire
      sameSite: 'strict',
      path: '/'
    });

    return res.status(200).json({
      message: "Logged out successfully",
      success: true
    });
  } catch (error) {
    console.log(error);
    return res.status(500).json({
      message: "Error during logout",
      success: false
    });
  }
};