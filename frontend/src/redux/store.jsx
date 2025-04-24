import {configureStore} from "@reduxjs/toolkit"
import userslice from "../redux/userslice"
import authSlice from "../redux/authSlice"

const store = configureStore({
    reducer:{
        user:userslice,
        auth:authSlice
    }
})

export default store;