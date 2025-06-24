import * as React from "react"
import { motion, useMotionValue, useTransform, animate } from "framer-motion"
import { TrendingUp, TrendingDown, Minus } from "lucide-react"
import { cn } from "@/lib/utils"
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

export function MetricCard({
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
  className,
  ...props
}: MetricCardProps) {
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
    <Card className={cn("relative overflow-hidden", className)} {...props}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
        </CardTitle>
        {icon && (
          <div className={cn("h-8 w-8 flex items-center justify-center rounded-full bg-primary/10", colorClasses[color])}>
            {icon}
          </div>
        )}
      </CardHeader>
      <CardContent>
        <div className="flex items-baseline justify-between">
          <div className="space-y-1">
            {loading ? (
              <div className="h-8 w-32 bg-muted animate-pulse rounded" />
            ) : (
              <motion.div className={cn("text-2xl font-bold", colorClasses[color])}>
                {shouldAnimate && typeof value === 'number' ? rounded : `${prefix}${value}${suffix}`}
              </motion.div>
            )}
            {(change !== undefined || changeLabel) && !loading && (
              <div className="flex items-center gap-1">
                {getTrendIcon()}
                <span className={cn("text-xs", getChangeColor())}>
                  {change !== undefined && `${change > 0 ? '+' : ''}${change}%`}
                </span>
                {changeLabel && (
                  <span className="text-xs text-muted-foreground">
                    {changeLabel}
                  </span>
                )}
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
