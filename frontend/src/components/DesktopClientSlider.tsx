import { useState, useEffect, useRef } from 'react';

interface SlideImage {
  src: string;
  alt: string;
  caption?: string;
}

const DESKTOP_IMAGES: SlideImage[] = [
  { src: '/SliderImages/DesktopClient.JPG', alt: 'Desktop Client 1', caption: 'Professional Trading Terminal - Live Games View' },
  { src: '/SliderImages/Desktopclient2.jpg', alt: 'Desktop Client 2', caption: 'Multi-Window Support - Analytics Dashboard' },
  { src: '/SliderImages/DesktopClient3.JPG', alt: 'Desktop Client 3', caption: 'Real-Time Alerts & Notifications' },
  { src: '/SliderImages/DesktopClient4.JPG', alt: 'Desktop Client 4', caption: 'Advanced Betting Strategies & Tools' },
];

export function DesktopClientSlider() {
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const [isAutoScrolling, setIsAutoScrolling] = useState(true);

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
        className="absolute left-0 top-1/2 -translate-y-1/2 z-10 bg-purple-600/80 hover:bg-purple-600 text-white p-3 rounded-full transition-all hover:scale-110 shadow-lg"
        aria-label="Scroll left"
      >
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M15 19l-7-7 7-7" />
        </svg>
      </button>
      <button
        onClick={scrollRight}
        className="absolute right-0 top-1/2 -translate-y-1/2 z-10 bg-purple-600/80 hover:bg-purple-600 text-white p-3 rounded-full transition-all hover:scale-110 shadow-lg"
        aria-label="Scroll right"
      >
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M9 5l7 7-7 7" />
        </svg>
      </button>

      {/* Scrollable Container */}
      <div
        ref={scrollContainerRef}
        className="flex gap-6 overflow-x-auto scroll-smooth pb-4 px-12"
        style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
        onMouseEnter={() => setIsAutoScrolling(false)}
        onMouseLeave={() => setIsAutoScrolling(true)}
      >
        {DESKTOP_IMAGES.map((image, index) => (
          <div
            key={index}
            className="flex-shrink-0 w-96 bg-slate-900/50 rounded-xl overflow-hidden border-2 border-purple-500/30 hover:border-purple-400 transition-all shadow-lg hover:shadow-xl hover:shadow-purple-500/30"
          >
            <img
              src={image.src}
              alt={image.alt}
              className="w-full h-auto object-contain"
            />
            {image.caption && (
              <div className="p-4 bg-slate-900/80">
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
          className="flex items-center gap-2 px-4 py-2 bg-purple-600/20 hover:bg-purple-600/30 text-purple-300 rounded-lg transition-all text-sm font-semibold border border-purple-500/30"
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
    </div>
  );
}
