import * as React from "react"
import { motion, useMotionValue, useTransform, animate } from "framer-motion"
import { TrendingUp, TrendingDown, Minus } from "lucide-react"
import { cn } from "../utils/cn"
import { Card, CardContent, CardHeader, CardTitle } from "./card"

interface MetricCardProps extends React.HTMLAttributes<HTMLDivElement> {
  title: string
  value: number | string
  change?: number
  changeLabel?: string
  icon?: React.ReactNode
  color?: "default" | "success" | "warning" | "danger" | "info"
  animate?: boolean
  prefix?: string
  suffix?: string
  loading?: boolean
}

const colorClasses = {
  default: "text-foreground",
  success: "text-green-500",
  warning: "text-yellow-500",
  danger: "text-red-500",
  info: "text-blue-500",
}

const MetricCard = React.forwardRef<HTMLDivElement, MetricCardProps>(
  ({
    className,
    title,
    value,
    change,
    changeLabel,
    icon,
    color = "default",
    animate: shouldAnimate = true,
    prefix = "",
    suffix = "",
    loading = false,
    ...props
  }, ref) => {
    const count = useMotionValue(0)
    const rounded = useTransform(count, (latest) => {
      const formatted = typeof value === 'number'
        ? Math.round(latest).toLocaleString()
        : value
      return `${prefix}${formatted}${suffix}`
    })

    React.useEffect(() => {
      if (shouldAnimate && typeof value === 'number' && !loading) {
        const animation = animate(count, value, {
          duration: 2,
          ease: "easeOut"
        })
        return animation.stop
      }
    }, [count, value, shouldAnimate, loading])

    const getTrendIcon = () => {
      if (!change) return <Minus className="h-4 w-4 text-muted-foreground" />
      if (change > 0) return <TrendingUp className="h-4 w-4 text-green-500" />
      return <TrendingDown className="h-4 w-4 text-red-500" />
    }

    const getChangeColor = () => {
      if (!change) return "text-muted-foreground"
      return change > 0 ? "text-green-500" : "text-red-500"
    }

    return (
      <Card
        ref={ref}
        className={cn("relative overflow-hidden", className)}
        hover="lift"
        {...props}
      >
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            {title}
          </CardTitle>
          {icon && (
            <motion.div
              whileHover={{ rotate: 360 }}
              transition={{ duration: 0.5 }}
              className={cn("h-8 w-8 flex items-center justify-center rounded-full bg-primary/10", colorClasses[color])}
            >
              {icon}
            </motion.div>
          )}
        </CardHeader>
        <CardContent>
          <div className="flex items-baseline justify-between">
            <div className="space-y-1">
              {loading ? (
                <div className="h-8 w-32 bg-muted animate-pulse rounded" />
              ) : (
                <motion.div
                  className={cn("text-2xl font-bold", colorClasses[color])}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5 }}
                >
                  {shouldAnimate && typeof value === 'number' ? rounded : `${prefix}${value}${suffix}`}
                </motion.div>
              )}
              {(change !== undefined || changeLabel) && !loading && (
                <motion.div
                  className="flex items-center gap-1"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.5 }}
                >
                  {getTrendIcon()}
                  <span className={cn("text-xs", getChangeColor())}>
                    {change !== undefined && `${change > 0 ? '+' : ''}${change}%`}
                  </span>
                  {changeLabel && (
                    <span className="text-xs text-muted-foreground">
                      {changeLabel}
                    </span>
                  )}
                </motion.div>
              )}
            </div>
          </div>
        </CardContent>

        {/* Background decoration */}
        <motion.div
          className="absolute -right-4 -top-4 h-24 w-24 rounded-full bg-gradient-to-br from-primary/20 to-primary/5"
          animate={{
            scale: [1, 1.2, 1],
            opacity: [0.3, 0.2, 0.3],
          }}
          transition={{
            duration: 4,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        />
      </Card>
    )
  }
)
MetricCard.displayName = "MetricCard"

export { MetricCard }
