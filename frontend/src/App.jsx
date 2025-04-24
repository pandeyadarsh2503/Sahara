import Features from "./components/Features";
import Footer from "./components/Footer";
import Home from "./components/Home"
import Login from "./components/Login";
import Nav from "./components/Nav";
import Signup from "./components/Signup"; 
import { Navigate, Route, Routes } from "react-router-dom";

const user = true; 

// function App() {
//   return (
//     <>
//       <Routes>
//         {!user ? (
//           <>
//             <Route path="/signup" element={<Signup />} />
//             <Route path="/login" element={<Login />} />
//             <Route path="*" element={<Navigate to="/login" />} />
//           </>
//         ) : (
//           <>
//             <Route path="/" element={<Nav />} />
//             <Route path="*" element={<Navigate to="/" />} />
//           </>
//         )}
//       </Routes>
//     </>
//   );
// }

function App() {
  return (
    <>
      <Routes>
        
          <>
            <Route path="/signup" element={<Signup />} />
            <Route path="/login" element={<Login />} />
            <Route path="/home" element={<Home />} />
            {/* <Route path="*" element={<Navigate to="/login" />} /> */}
          </>
        
          <>
            <Route path="/" element={<Nav />} />
            {/* <Route path="*" element={<Navigate to="/" />} /> */}
          </>
        
      </Routes>
    </>
  );
}

export default App;