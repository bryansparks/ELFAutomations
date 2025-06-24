import * as React from "react"
import { motion } from "framer-motion"
import { cn } from "@/lib/utils"

interface LoadingProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "dots" | "pulse" | "wave" | "orbit"
  size?: "sm" | "md" | "lg"
  color?: "primary" | "secondary" | "gradient"
}

const sizeClasses = {
  sm: "h-8 w-8",
  md: "h-12 w-12",
  lg: "h-16 w-16"
}

export function Loading({
  className,
  variant = "dots",
  size = "md",
  color = "primary",
  ...props
}: LoadingProps) {
  const renderVariant = () => {
    switch (variant) {
      case "dots":
        return (
          <div className="flex space-x-2">
            {[0, 1, 2].map((i) => (
              <motion.div
                key={i}
                className="h-3 w-3 rounded-full bg-primary"
                animate={{
                  scale: [1, 1.5, 1],
                  opacity: [1, 0.5, 1],
                }}
                transition={{
                  duration: 1.5,
                  repeat: Infinity,
                  delay: i * 0.2,
                  ease: "easeInOut"
                }}
              />
            ))}
          </div>
        )

      case "pulse":
        return (
          <motion.div
            className={cn(sizeClasses[size], "rounded-full bg-primary")}
            animate={{
              scale: [1, 1.2, 1],
              opacity: [0.5, 0.3, 0.5],
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: "easeInOut"
            }}
          />
        )

      case "wave":
        return (
          <div className="flex space-x-1">
            {[0, 1, 2, 3, 4].map((i) => (
              <motion.div
                key={i}
                className="w-1 bg-primary rounded-full"
                animate={{
                  height: ["12px", "24px", "12px"],
                }}
                transition={{
                  duration: 1,
                  repeat: Infinity,
                  delay: i * 0.15,
                  ease: "easeInOut"
                }}
              />
            ))}
          </div>
        )

      case "orbit":
        return (
          <div className={cn(sizeClasses[size], "relative")}>
            <motion.div
              className="absolute inset-0 rounded-full border-2 border-primary"
              style={{ borderTopColor: "transparent" }}
              animate={{ rotate: 360 }}
              transition={{
                duration: 1,
                repeat: Infinity,
                ease: "linear"
              }}
            />
          </div>
        )

      default:
        return null
    }
  }

  return (
    <div ref={props.ref} className={cn("flex items-center justify-center", className)} {...props}>
      {renderVariant()}
    </div>
  )
}
