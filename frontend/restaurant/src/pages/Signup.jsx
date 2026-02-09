import { Box } from "@chakra-ui/react";

export default function Signup() {
    return (
        <Box>
            {/* const schema = z.object({
                username: z.string()
                    .min(3, "Username too short")
                    .max(20, "Username too long")
                    .regex(/^[a-zA-Z0-9_]+$/, "Only letters, numbers, and underscores allowed"),
                email: z.string().email("Invalid email"),
                password: z.string()
                    .min(8, "Password must be at least 8 characters")
                    .regex(/[A-Z]/, "Must contain an uppercase letter")
                    .regex(/[0-9]/, "Must contain a number"),

            }).refine((data) => data.password === data.confirmedPassword, {
                message: "Passwords must match",
                path: ["confirmedPassword"]
            }) */}
        </Box>
    )
}