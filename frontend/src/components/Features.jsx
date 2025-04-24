export default function Features() {
  const features = [
    {
      icon: "💊",
      title: "Medication Reminders",
      desc: "Never miss important medications with timely, gentle reminders from Sahara throughout the day.",
    },
    {
      icon: "📷",
      title: "Fall Detection",
      desc: "Advanced camera monitoring that respects privacy while ensuring safety and quick response to emergencies.",
    },
    {
      icon: "🔔",
      title: "Family Alerts",
      desc: "Keep loved ones informed with instant notifications about important events and potential concerns.",
    },
    {
      icon: "💬",
      title: "Casual Conversation",
      desc: "Enjoy friendly chats and companionship with Sahara, an AI that understands and responds with empathy.",
    },
    {
      icon: "🛡️",
      title: "Privacy First",
      desc: "State-of-the-art encryption and privacy protection ensures personal data stays secure and private.",
    },
    {
      icon: "💜",
      title: "24/7 Care",
      desc: "Round-the-clock monitoring and assistance from Sahara for complete peace of mind.",
    },
  ];

  return (
    <section className="bg-gradient-to-b from-[#f0f4ff] via-white to-[#f0f4ff] py-20 px-6">
      <h2 className="text-center text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-purple-600 to-blue-600 mb-14">
        Features that Care 💖
      </h2>
      <div className="grid md:grid-cols-3 sm:grid-cols-2 gap-8 max-w-6xl mx-auto px-2">
        {features.map((f, i) => (
          <div
            key={i}
            className="bg-white rounded-2xl p-6 shadow-md hover:shadow-lg transition-all duration-300 border-t-4 border-purple-200 hover:border-purple-500"
          >
            <div className="text-4xl mb-4">{f.icon}</div>
            <h3 className="text-xl font-semibold text-indigo-700 mb-2">{f.title}</h3>
            <p className="text-gray-600 text-sm leading-relaxed">{f.desc}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
