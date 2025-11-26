import { useState, useEffect, useRef } from 'react';

interface SlideImage {
  src: string;
  alt: string;
  caption: string;
}

const PARTNER_IMAGES: SlideImage[] = [
  { src: '/PartnerImages/Partner_Login.JPG', alt: 'Partner Login', caption: 'Secure Partner Portal Login' },
  { src: '/PartnerImages/Partner_Portal.JPG', alt: 'Partner Portal Dashboard', caption: 'Real-Time Earnings Dashboard' },
  { src: '/PartnerImages/Partner_User_Table.JPG', alt: 'Partner User Table', caption: 'Track Your Referrals & Commissions' },
];

export function PartnerImageSlider() {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isEnlarged, setIsEnlarged] = useState(false);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    // Auto-scroll every 3 seconds
    intervalRef.current = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % PARTNER_IMAGES.length);
    }, 3000);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  const goToSlide = (index: number) => {
    setCurrentIndex(index);
    // Reset timer when manually navigating
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = setInterval(() => {
        setCurrentIndex((prev) => (prev + 1) % PARTNER_IMAGES.length);
      }, 3000);
    }
  };

  const currentImage = PARTNER_IMAGES[currentIndex];

  return (
    <>
      <div className="relative w-full max-w-4xl mx-auto">
        {/* Main image */}
        <div
          className="relative overflow-hidden rounded-lg border-2 border-slate-700 cursor-pointer hover:border-blue-500 transition-all"
          onClick={() => setIsEnlarged(true)}
        >
          <img
            src={currentImage.src}
            alt={currentImage.alt}
            className="w-full h-auto object-contain"
          />
          <div className="absolute bottom-0 left-0 right-0 bg-black/70 p-3">
            <p className="text-slate-200 text-sm font-medium text-center">{currentImage.caption}</p>
          </div>
        </div>

        {/* Dots navigation */}
        <div className="flex justify-center gap-2 mt-4">
          {PARTNER_IMAGES.map((_, index) => (
            <button
              key={index}
              onClick={() => goToSlide(index)}
              className={`w-3 h-3 rounded-full transition-all ${
                index === currentIndex
                  ? 'bg-blue-500 w-8'
                  : 'bg-slate-600 hover:bg-slate-500'
              }`}
              aria-label={`Go to slide ${index + 1}`}
            />
          ))}
        </div>

        {/* Click to enlarge hint */}
        <p className="text-slate-500 text-xs text-center mt-2">Click image to enlarge</p>
      </div>

      {/* Enlarged view modal */}
      {isEnlarged && (
        <div
          className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center p-4"
          onClick={() => setIsEnlarged(false)}
        >
          <div className="relative max-w-7xl max-h-[90vh]">
            <img
              src={currentImage.src}
              alt={currentImage.alt}
              className="max-w-full max-h-[90vh] object-contain"
            />
            <button
              onClick={() => setIsEnlarged(false)}
              className="absolute top-4 right-4 text-white bg-black/50 hover:bg-black/70 rounded-full w-10 h-10 flex items-center justify-center text-2xl font-bold"
            >
              ×
            </button>
          </div>
        </div>
      )}
    </>
  );
}
