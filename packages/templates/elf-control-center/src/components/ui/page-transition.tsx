import * as React from "react"
import { motion, AnimatePresence } from "framer-motion"
import { cn } from "@/lib/utils"

interface PageTransitionProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "fade" | "slide" | "scale"
  direction?: "left" | "right" | "up" | "down"
  duration?: number
}

const variants = {
  fade: {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    exit: { opacity: 0 }
  },
  slide: {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: -20 }
  },
  scale: {
    initial: { scale: 0.9, opacity: 0 },
    animate: { scale: 1, opacity: 1 },
    exit: { scale: 1.1, opacity: 0 }
  }
}

export function PageTransition({
  children,
  variant = "fade",
  duration = 0.3,
  className,
  ...props
}: PageTransitionProps) {
  return (
    <motion.div
      className={cn("w-full", className)}
      variants={variants[variant]}
      initial="initial"
      animate="animate"
      exit="exit"
      transition={{ duration }}
      {...props}
    >
      {children}
    </motion.div>
  )
}
