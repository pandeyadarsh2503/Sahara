import { useNavigate } from "react-router-dom";
import Features from "./Features";
import Footer from "./Footer";
import Navbar from "./Navbar";

export default function Nav() {
  const navigate = useNavigate();

  return (
    <div className="bg-[#f0f4ff] text-gray-900 min-h-screen">
      <Navbar />

      {/* Hero Section */}
      <section className="text-center py-28 px-6 bg-gradient-to-br from-indigo-100 via-blue-200 to-purple-100">
        <h1 className="text-5xl font-extrabold mb-6 text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-purple-700 drop-shadow-md">
          Meet Sahara
        </h1>

        <p className="text-lg max-w-2xl mx-auto mb-3 text-gray-700">
          Your caring AI companion empowering seniors to live independently with dignity and peace of mind.
        </p>
        <p className="text-md text-gray-600 mb-8">
          Sahara watches out for their well-being, always.
        </p>

        <div className="flex justify-center gap-4">
          <button
            onClick={() => navigate("/home")}
            className="bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 transition-all duration-200 text-white px-8 py-3 rounded-full text-sm font-medium shadow-lg"
          >
            Get Started
          </button>
          <button
            className="bg-white hover:bg-gray-100 text-purple-700 px-8 py-3 rounded-full text-sm font-medium border border-purple-300 shadow"
          >
            Learn More
          </button>
        </div>
      </section>

      <Features />
      <Footer />
    </div>
  );
}
