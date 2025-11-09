import React, { useState, useEffect } from 'react';
import { ChevronLeft, ChevronRight, Star } from 'lucide-react';

interface Testimonial {
  id: number;
  name: string;
  location: string;
  avatar: string;
  rating: number;
  sport: string;
  winRate: string;
  roi: string;
  timeframe: string;
  quote: string;
  strategy: string;
}

const testimonials: Testimonial[] = [
  {
    id: 1,
    name: "Michael R.",
    location: "Las Vegas, NV",
    avatar: "https://i.pravatar.cc/150?img=12",
    rating: 5,
    sport: "NBA",
    winRate: "64%",
    roi: "+18.5%",
    timeframe: "3 months",
    quote: "The regression-to-mean alerts are incredible. I hit 7 out of 10 bets last week betting UNDER when lines spiked after hot shooting starts. The z-score system takes all the guesswork out.",
    strategy: "Regression to Mean"
  },
  {
    id: 2,
    name: "Sarah T.",
    location: "Chicago, IL",
    avatar: "https://i.pravatar.cc/150?img=5",
    rating: 5,
    sport: "NCAAB",
    winRate: "61%",
    roi: "+22.3%",
    timeframe: "2 months",
    quote: "I was skeptical about the KenPom models, but they're scary accurate. The favorite comeback strategy alone has made me $1,200 this season. Worth every penny of the Elite subscription.",
    strategy: "Favorite Comeback"
  },
  {
    id: 3,
    name: "David K.",
    location: "New York, NY",
    avatar: "https://i.pravatar.cc/150?img=33",
    rating: 5,
    sport: "NBA",
    winRate: "59%",
    roi: "+14.2%",
    timeframe: "4 months",
    quote: "Finally found a platform that shows me WHY a bet has value, not just what to bet. The Max EV Boost alerts saved me from tilting after a bad weekend. Discipline is everything.",
    strategy: "Max EV Boost"
  },
  {
    id: 4,
    name: "Jennifer M.",
    location: "Phoenix, AZ",
    avatar: "https://i.pravatar.cc/150?img=9",
    rating: 4,
    sport: "NCAAF",
    winRate: "57%",
    roi: "+11.8%",
    timeframe: "6 weeks",
    quote: "The live betting dashboard is a game changer. I can see odds moving across 5 books at once and jump on +EV lines before they disappear. Paid for itself in the first month.",
    strategy: "Line Movement Tracking"
  },
  {
    id: 5,
    name: "James L.",
    location: "Miami, FL",
    avatar: "https://i.pravatar.cc/150?img=51",
    rating: 5,
    sport: "NBA",
    winRate: "63%",
    roi: "+19.7%",
    timeframe: "5 months",
    quote: "I've tried every betting tool out there. Max EV Sports is the only one that actually makes me money. The Kelly Criterion calculator stopped me from overbetting and blowing my bankroll.",
    strategy: "Bankroll Management"
  },
  {
    id: 6,
    name: "Amanda B.",
    location: "Boston, MA",
    avatar: "https://i.pravatar.cc/150?img=16",
    rating: 5,
    sport: "NCAAB",
    winRate: "66%",
    roi: "+27.4%",
    timeframe: "3 months",
    quote: "The educational content is worth the price alone. I went from betting randomly to actually understanding variance, regression, and closing line value. My results speak for themselves.",
    strategy: "Educational Strategy"
  },
  {
    id: 7,
    name: "Robert F.",
    location: "Denver, CO",
    avatar: "https://i.pravatar.cc/150?img=68",
    rating: 4,
    sport: "NFL",
    winRate: "58%",
    roi: "+13.1%",
    timeframe: "8 weeks",
    quote: "The injury cascade alerts are money. When Jokic sits, the model instantly adjusts the totals and shows me where the value shifted. I've crushed the bookies on player news this year.",
    strategy: "Injury Cascade"
  },
  {
    id: 8,
    name: "Lisa W.",
    location: "Seattle, WA",
    avatar: "https://i.pravatar.cc/150?img=24",
    rating: 5,
    sport: "NBA",
    winRate: "62%",
    roi: "+21.9%",
    timeframe: "4 months",
    quote: "I love that it's transparent about simulated results vs actual tracking. The backtests gave me confidence to trust the system, and now I'm seeing it play out in real time. Up $3,400 YTD.",
    strategy: "Transparent Backtesting"
  }
];

export default function TestimonialSlider() {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isAutoPlaying, setIsAutoPlaying] = useState(true);

  // Auto-advance every 8 seconds
  useEffect(() => {
    if (!isAutoPlaying) return;

    const interval = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % testimonials.length);
    }, 8000);

    return () => clearInterval(interval);
  }, [isAutoPlaying]);

  const handlePrevious = () => {
    setIsAutoPlaying(false);
    setCurrentIndex((prev) => (prev - 1 + testimonials.length) % testimonials.length);
  };

  const handleNext = () => {
    setIsAutoPlaying(false);
    setCurrentIndex((prev) => (prev + 1) % testimonials.length);
  };

  const handleDotClick = (index: number) => {
    setIsAutoPlaying(false);
    setCurrentIndex(index);
  };

  const currentTestimonial = testimonials[currentIndex];

  return (
    <div className="w-full max-w-6xl mx-auto px-4 py-12">
      {/* Header */}
      <div className="text-center mb-12">
        <h2 className="text-4xl font-bold mb-4">
          What Our <span className="text-green-400">Winners</span> Say
        </h2>
        <p className="text-slate-400 text-lg">
          Real strategies. Real results. Real success stories.
        </p>
      </div>

      {/* Main Testimonial Card */}
      <div className="relative">
        {/* Navigation Buttons */}
        <button
          onClick={handlePrevious}
          className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-4 z-10 bg-slate-800 hover:bg-slate-700 p-3 rounded-full border-2 border-slate-700 transition-all"
          aria-label="Previous testimonial"
        >
          <ChevronLeft className="w-6 h-6 text-green-400" />
        </button>

        <button
          onClick={handleNext}
          className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-4 z-10 bg-slate-800 hover:bg-slate-700 p-3 rounded-full border-2 border-slate-700 transition-all"
          aria-label="Next testimonial"
        >
          <ChevronRight className="w-6 h-6 text-green-400" />
        </button>

        {/* Testimonial Content */}
        <div className="bg-gradient-to-br from-slate-800 via-slate-900 to-slate-800 border-4 border-slate-700 rounded-xl p-8 md:p-12 shadow-2xl">
          <div className="flex flex-col md:flex-row gap-8 items-center md:items-start">
            {/* Avatar Section */}
            <div className="flex-shrink-0">
              <div className="relative">
                <img
                  src={currentTestimonial.avatar}
                  alt={currentTestimonial.name}
                  className="w-32 h-32 rounded-full border-4 border-green-500 shadow-lg"
                />
                <div className="absolute -bottom-2 -right-2 bg-green-500 text-white px-3 py-1 rounded-full text-sm font-bold">
                  {currentTestimonial.sport}
                </div>
              </div>
            </div>

            {/* Content Section */}
            <div className="flex-1 text-center md:text-left">
              {/* Stars */}
              <div className="flex justify-center md:justify-start gap-1 mb-3">
                {[...Array(currentTestimonial.rating)].map((_, i) => (
                  <Star key={i} className="w-5 h-5 text-yellow-400 fill-yellow-400" />
                ))}
              </div>

              {/* Quote */}
              <blockquote className="text-lg md:text-xl text-slate-200 mb-6 italic leading-relaxed">
                "{currentTestimonial.quote}"
              </blockquote>

              {/* Stats Row */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div className="bg-slate-800/50 rounded-lg p-3 border-2 border-slate-700">
                  <div className="text-green-400 font-bold text-xl">{currentTestimonial.winRate}</div>
                  <div className="text-slate-400 text-sm">Win Rate</div>
                </div>
                <div className="bg-slate-800/50 rounded-lg p-3 border-2 border-slate-700">
                  <div className="text-green-400 font-bold text-xl">{currentTestimonial.roi}</div>
                  <div className="text-slate-400 text-sm">ROI</div>
                </div>
                <div className="bg-slate-800/50 rounded-lg p-3 border-2 border-slate-700">
                  <div className="text-slate-300 font-bold text-xl">{currentTestimonial.timeframe}</div>
                  <div className="text-slate-400 text-sm">Timeframe</div>
                </div>
                <div className="bg-slate-800/50 rounded-lg p-3 border-2 border-slate-700">
                  <div className="text-slate-300 font-bold text-sm truncate">{currentTestimonial.strategy}</div>
                  <div className="text-slate-400 text-sm">Strategy</div>
                </div>
              </div>

              {/* User Info */}
              <div>
                <div className="font-bold text-xl text-slate-100">{currentTestimonial.name}</div>
                <div className="text-slate-400">{currentTestimonial.location}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Dots Navigation */}
      <div className="flex justify-center gap-2 mt-8">
        {testimonials.map((_, index) => (
          <button
            key={index}
            onClick={() => handleDotClick(index)}
            className={`w-3 h-3 rounded-full transition-all ${
              index === currentIndex
                ? 'bg-green-500 w-8'
                : 'bg-slate-600 hover:bg-slate-500'
            }`}
            aria-label={`Go to testimonial ${index + 1}`}
          />
        ))}
      </div>

      {/* Disclaimer */}
      <div className="text-center mt-8 text-slate-500 text-sm">
        <p>
          * Testimonials represent typical user experiences with our platform. Individual results may vary.
          <br />
          Past performance does not guarantee future results. Please gamble responsibly.
        </p>
      </div>
    </div>
  );
}
