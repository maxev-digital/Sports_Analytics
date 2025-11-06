import { useState, useEffect, useRef } from 'react';

interface SlideImage {
  src: string;
  alt: string;
  caption?: string;
}

const SLIDER_IMAGES: SlideImage[] = [
  { src: '/SliderImages/Analytics.JPG', alt: 'Analytics Dashboard', caption: 'Advanced Analytics & Performance Tracking' },
  { src: '/SliderImages/ExtensionImage.JPG', alt: 'Extension Features', caption: 'Browser Extension Live Odds Integration' },
  { src: '/SliderImages/BookmakerSettings.JPG', alt: 'Bookmaker Settings', caption: 'Customize Your Sportsbook Preferences' },
  { src: '/SliderImages/Education.JPG', alt: 'Education Center', caption: 'Learn Winning Betting Strategies' },
  { src: '/SliderImages/GameCardNFL.JPG', alt: 'NFL Game Card', caption: 'NFL Live Game Tracking' },
  { src: '/SliderImages/GameCardNHL.JPG', alt: 'NHL Game Card', caption: 'NHL In-Game Betting Opportunities' },
  { src: '/SliderImages/GettingStarted.JPG', alt: 'Getting Started', caption: 'Quick Start Guide & Onboarding' },
  { src: '/SliderImages/Props.JPG', alt: 'Player Props', caption: 'Player Props Analysis & Projections' },
  { src: '/SliderImages/Strategies.JPG', alt: 'Betting Strategies', caption: 'Pre-Game & Live Betting Strategies' },
];

export function ImageSlider() {
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const [isAutoScrolling, setIsAutoScrolling] = useState(true);
  const [selectedImage, setSelectedImage] = useState<SlideImage | null>(null);

  // Auto-scroll functionality
  useEffect(() => {
    if (!isAutoScrolling) return;

    const interval = setInterval(() => {
      if (scrollContainerRef.current) {
        const container = scrollContainerRef.current;
        const maxScroll = container.scrollWidth - container.clientWidth;

        // If we're at the end, reset to beginning
        if (container.scrollLeft >= maxScroll - 10) {
          container.scrollTo({ left: 0, behavior: 'smooth' });
        } else {
          // Scroll right by 400px
          container.scrollBy({ left: 400, behavior: 'smooth' });
        }
      }
    }, 3000); // Auto-scroll every 3 seconds

    return () => clearInterval(interval);
  }, [isAutoScrolling]);

  const scrollLeft = () => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollBy({ left: -400, behavior: 'smooth' });
      setIsAutoScrolling(false); // Pause auto-scroll when user interacts
    }
  };

  const scrollRight = () => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollBy({ left: 400, behavior: 'smooth' });
      setIsAutoScrolling(false); // Pause auto-scroll when user interacts
    }
  };

  return (
    <div className="relative w-full">
      {/* Navigation Arrows */}
      <button
        onClick={scrollLeft}
        className="absolute left-0 top-1/2 -translate-y-1/2 z-10 bg-black/70 hover:bg-black/90 text-white p-3 rounded-full transition-all hover:scale-110 shadow-lg"
        aria-label="Scroll left"
      >
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M15 19l-7-7 7-7" />
        </svg>
      </button>
      <button
        onClick={scrollRight}
        className="absolute right-0 top-1/2 -translate-y-1/2 z-10 bg-black/70 hover:bg-black/90 text-white p-3 rounded-full transition-all hover:scale-110 shadow-lg"
        aria-label="Scroll right"
      >
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M9 5l7 7-7 7" />
        </svg>
      </button>

      {/* Scrollable Container */}
      <div
        ref={scrollContainerRef}
        className="flex gap-4 overflow-x-auto scroll-smooth pb-4 px-12"
        style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
        onMouseEnter={() => setIsAutoScrolling(false)}
        onMouseLeave={() => setIsAutoScrolling(true)}
      >
        {SLIDER_IMAGES.map((image, index) => (
          <div
            key={index}
            onClick={() => setSelectedImage(image)}
            className="flex-shrink-0 w-80 bg-slate-800 rounded-xl overflow-hidden border-2 border-slate-700 hover:border-blue-500 transition-all shadow-lg hover:shadow-xl hover:shadow-blue-500/20 cursor-pointer group"
          >
            <div className="relative">
              <img
                src={image.src}
                alt={image.alt}
                className="w-full h-auto object-contain"
              />
              {/* Click to enlarge overlay */}
              <div className="absolute inset-0 bg-black/0 group-hover:bg-black/40 transition-all flex items-center justify-center">
                <div className="opacity-0 group-hover:opacity-100 transition-all">
                  <svg className="w-12 h-12 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7" />
                  </svg>
                  <p className="text-white font-bold text-sm mt-2">Click to Enlarge</p>
                </div>
              </div>
            </div>
            {image.caption && (
              <div className="p-4 bg-slate-900">
                <p className="text-slate-200 text-sm font-semibold text-center">
                  {image.caption}
                </p>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Auto-scroll indicator */}
      <div className="flex justify-center mt-4">
        <button
          onClick={() => setIsAutoScrolling(!isAutoScrolling)}
          className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition-all text-sm font-semibold border border-slate-700"
        >
          {isAutoScrolling ? (
            <>
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z" />
              </svg>
              Pause Auto-Scroll
            </>
          ) : (
            <>
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                <path d="M8 5v14l11-7z" />
              </svg>
              Resume Auto-Scroll
            </>
          )}
        </button>
      </div>

      {/* Hide scrollbar with CSS */}
      <style>{`
        .overflow-x-auto::-webkit-scrollbar {
          display: none;
        }
      `}</style>

      {/* Image Modal */}
      {selectedImage && (
        <div
          onClick={() => setSelectedImage(null)}
          className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center p-4 cursor-pointer"
        >
          <div className="relative max-w-6xl w-full max-h-[90vh] flex flex-col">
            {/* Close button */}
            <button
              onClick={() => setSelectedImage(null)}
              className="absolute -top-12 right-0 bg-white/10 hover:bg-white/20 text-white p-2 rounded-full transition-all"
              aria-label="Close"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>

            {/* Image */}
            <div className="bg-slate-800 rounded-xl overflow-hidden border-2 border-blue-500 shadow-2xl">
              <img
                src={selectedImage.src}
                alt={selectedImage.alt}
                className="w-full h-auto object-contain max-h-[80vh]"
                onClick={(e) => e.stopPropagation()}
              />
              {selectedImage.caption && (
                <div className="p-6 bg-slate-900">
                  <p className="text-slate-100 text-lg font-semibold text-center">
                    {selectedImage.caption}
                  </p>
                </div>
              )}
            </div>

            {/* Instructions */}
            <p className="text-slate-400 text-center mt-4 text-sm">
              Click anywhere to close
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
