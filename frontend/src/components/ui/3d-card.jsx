import React, {
  createContext,
  useState,
  useContext,
  useRef,
  useEffect,
  useMemo,
} from "react";
import { twMerge } from "tailwind-merge";

// Clean, compile-safe tailwind class merger utility
function cn(...inputs) {
  return twMerge(inputs.filter(Boolean).join(" "));
}

const MouseEnterContext = createContext(undefined);

/**
 * CardContainer - Outer wrapper setting up the 3D perspective field and event listeners.
 */
export const CardContainer = ({
  children,
  className = "",
  containerClassName = "",
}) => {
  const containerRef = useRef(null);
  const [isMouseEntered, setIsMouseEntered] = useState(false);

  const handleMouseMove = (e) => {
    if (!containerRef.current) return;
    const { left, top, width, height } =
      containerRef.current.getBoundingClientRect();
    const x = (e.clientX - left - width / 2) / 20; // 20 is tilt sensitivity
    const y = (e.clientY - top - height / 2) / 20;
    containerRef.current.style.transform = `rotateY(${x}deg) rotateX(${-y}deg)`;
  };

  const handleMouseEnter = () => {
    setIsMouseEntered(true);
  };

  const handleMouseLeave = () => {
    if (!containerRef.current) return;
    setIsMouseEntered(false);
    containerRef.current.style.transform = `rotateY(0deg) rotateX(0deg)`;
  };

  const contextValue = useMemo(() => [isMouseEntered, setIsMouseEntered], [isMouseEntered]);

  return (
    <MouseEnterContext.Provider value={contextValue}>
      <div
        className={cn("flex items-center justify-center w-full", containerClassName)}
        style={{
          perspective: "1000px",
        }}
      >
        <div
          ref={containerRef}
          onMouseEnter={handleMouseEnter}
          onMouseMove={handleMouseMove}
          onMouseLeave={handleMouseLeave}
          className={cn(
            "relative transition-all duration-200 ease-linear w-full h-full",
            className
          )}
          style={{
            transformStyle: "preserve-3d",
          }}
        >
          {children}
        </div>
      </div>
    </MouseEnterContext.Provider>
  );
};

/**
 * CardBody - Intermediate card body holding 3D transformation constraints.
 */
export const CardBody = ({ children, className = "" }) => {
  return (
    <div
      className={cn(
        "[transform-style:preserve-3d] [&>*]:[transform-style:preserve-3d] w-full h-full",
        className
      )}
    >
      {children}
    </div>
  );
};

/**
 * CardItem - Individual animated component translating elements along Z, X, Y axes inside the 3D card.
 */
export const CardItem = ({
  as: Component = "div",
  children,
  className = "",
  translateX = 0,
  translateY = 0,
  translateZ = 0,
  rotateX = 0,
  rotateY = 0,
  rotateZ = 0,
  ...rest
}) => {
  const ref = useRef(null);
  const context = useContext(MouseEnterContext);
  const [isMouseEntered] = context || [false];

  useEffect(() => {
    if (!ref.current) return;
    if (isMouseEntered) {
      ref.current.style.transform = `translateX(${translateX}px) translateY(${translateY}px) translateZ(${translateZ}px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) rotateZ(${rotateZ}deg)`;
    } else {
      ref.current.style.transform = `translateX(0px) translateY(0px) translateZ(0px) rotateX(0deg) rotateY(0deg) rotateZ(0deg)`;
    }
  }, [isMouseEntered, translateX, translateY, translateZ, rotateX, rotateY, rotateZ]);

  return (
    <Component
      ref={ref}
      className={cn("transition duration-200 ease-linear", className)}
      {...rest}
    >
      {children}
    </Component>
  );
};

export const useMouseEnter = () => {
  const context = useContext(MouseEnterContext);
  if (context === undefined) {
    throw new Error("useMouseEnter must be used within a MouseEnterProvider");
  }
  return context;
};
