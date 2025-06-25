import * as React from "react"
import { motion, AnimatePresence } from "framer-motion"
import { cn } from "../utils/cn"

interface PageTransitionProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "fade" | "slide" | "scale" | "rotate" | "morph"
  direction?: "left" | "right" | "up" | "down"
  duration?: number
  delay?: number
  exitBeforeEnter?: boolean
}

const variants = {
  fade: {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    exit: { opacity: 0 }
  },
  slide: {
    left: {
      initial: { x: "-100%", opacity: 0 },
      animate: { x: 0, opacity: 1 },
      exit: { x: "100%", opacity: 0 }
    },
    right: {
      initial: { x: "100%", opacity: 0 },
      animate: { x: 0, opacity: 1 },
      exit: { x: "-100%", opacity: 0 }
    },
    up: {
      initial: { y: "100%", opacity: 0 },
      animate: { y: 0, opacity: 1 },
      exit: { y: "-100%", opacity: 0 }
    },
    down: {
      initial: { y: "-100%", opacity: 0 },
      animate: { y: 0, opacity: 1 },
      exit: { y: "100%", opacity: 0 }
    }
  },
  scale: {
    initial: { scale: 0.8, opacity: 0 },
    animate: { scale: 1, opacity: 1 },
    exit: { scale: 1.2, opacity: 0 }
  },
  rotate: {
    initial: { rotate: -180, scale: 0.8, opacity: 0 },
    animate: { rotate: 0, scale: 1, opacity: 1 },
    exit: { rotate: 180, scale: 0.8, opacity: 0 }
  },
  morph: {
    initial: {
      clipPath: "circle(0% at 50% 50%)",
      opacity: 0
    },
    animate: {
      clipPath: "circle(100% at 50% 50%)",
      opacity: 1
    },
    exit: {
      clipPath: "circle(0% at 50% 50%)",
      opacity: 0
    }
  }
}

const PageTransition = React.forwardRef<HTMLDivElement, PageTransitionProps>(
  ({
    className,
    children,
    variant = "fade",
    direction = "right",
    duration = 0.3,
    delay = 0,
    exitBeforeEnter = false,
    ...props
  }, ref) => {
    const getVariant = () => {
      if (variant === "slide") {
        return variants.slide[direction]
      }
      return variants[variant]
    }

    return (
      <AnimatePresence mode={exitBeforeEnter ? "wait" : "sync"}>
        <motion.div
          ref={ref}
          className={cn("w-full", className)}
          variants={getVariant()}
          initial="initial"
          animate="animate"
          exit="exit"
          transition={{
            duration,
            delay,
            ease: [0.42, 0, 0.58, 1], // Custom easing
          }}
          {...props}
        >
          {children}
        </motion.div>
      </AnimatePresence>
    )
  }
)
PageTransition.displayName = "PageTransition"

// Stagger children animations
interface StaggerContainerProps extends React.HTMLAttributes<HTMLDivElement> {
  staggerDelay?: number
  animateOnce?: boolean
}

const StaggerContainer = React.forwardRef<HTMLDivElement, StaggerContainerProps>(
  ({ className, children, staggerDelay = 0.1, animateOnce = false, ...props }, ref) => {
    const containerVariants = {
      hidden: { opacity: 0 },
      visible: {
        opacity: 1,
        transition: {
          staggerChildren: staggerDelay,
        }
      }
    }

    const itemVariants = {
      hidden: { y: 20, opacity: 0 },
      visible: {
        y: 0,
        opacity: 1,
        transition: {
          type: "spring",
          stiffness: 100,
        }
      }
    }

    return (
      <motion.div
        ref={ref}
        className={cn("w-full", className)}
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        {...props}
      >
        {React.Children.map(children, (child, index) => (
          <motion.div key={index} variants={itemVariants}>
            {child}
          </motion.div>
        ))}
      </motion.div>
    )
  }
)
StaggerContainer.displayName = "StaggerContainer"

export { PageTransition, StaggerContainer }
