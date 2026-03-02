import { Box, Field, Input, Button, Flex } from "@chakra-ui/react";
import { toaster } from "../components/ui/toaster";
import { PasswordInput } from "../components/ui/password-input";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { useAuth } from "../contexts/AuthContext";
import { useNavigate } from "react-router-dom";
 
// Define the schema for the form
const schema = z.object({
    username: z.string()
            .min(3, "Username too short")
            .max(20, "Username too long")
            .regex(/^[a-zA-Z0-9_]+$/, "Only letters, numbers, and underscores allowed"),
    first_name: z.string(),
    last_name: z.string(),
    email: z.string().email("Invalid email"),
    password: z.string()
            .min(8, "Password must be at least 8 characters")
            .regex(/[A-Z]/, "Must contain an uppercase letter")
            .regex(/[0-9]/, "Must contain a number"),
    confirmedPassword: z.string(),

}).refine((data) => data.password === data.confirmedPassword, {
    message: "Passwords must match",
    path: ["confirmedPassword"]
})

export default function Signup() {
    // Get the callAPI function
    const { callAPI, login } = useAuth();

    // Get the navigate function
    const navigate = useNavigate();

    // Form Hook
    const {
        register,
        handleSubmit,
        formState: { errors }
    } = useForm({ resolver: zodResolver(schema), mode: 'onChange' });

    // Submit handler
    const mySubmitHandler = async (data) => {
        let res = null;
        try {
            res = await callAPI(
                '/auth/signup/',
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                }
            );
            if(!res.ok) throw new Error('callAPI successfully but res is not true');

            const loginRes = await login(data.username, data.password);
            if(loginRes.success) navigate('/');
            else {
                toaster.create({
                    title: res.message,
                    description: "Please try again or wait and try later",
                    type: "error",
                    closable: true
                });
            }
        }
        catch (e) {
            console.log(e.message);
        }
    };

    // Define the style of the form
    const style = {
        color: "gray.700",
        font: "cursive",
        fontSize: "1.5rem",
        gap: "3rem",
        buttonH: "3rem",
        buttonW: "8rem"
    };

    return (
        <Box mt="10vh" color={style.color} fontFamily="cursive" w="70vw" mx="auto">
            <form onSubmit={handleSubmit(mySubmitHandler)}>
                <Flex direction="column" gap={style.gap}>
                    <Field.Root invalid={!!errors.username} required>
                        <Field.Label fontSize={style.fontSize} mb="1rem">
                            Username
                            <Field.RequiredIndicator/>
                        </Field.Label>
                        <Input {...register("username")} size="xl" fontSize="1.3rem" bg="white"/>
                        <Field.ErrorText>{errors.username?.message}</Field.ErrorText>
                    </Field.Root>

                    <Field.Root  invalid={!!errors.first_name}>
                        <Field.Label fontSize={style.fontSize} mb="1rem">First Name</Field.Label>
                        <Input {...register("first_name")} size="xl" fontSize="1.3rem" bg="white"/>
                        <Field.ErrorText>{errors.firstName?.message}</Field.ErrorText>
                    </Field.Root>

                    <Field.Root  invalid={!!errors.last_name}>
                        <Field.Label fontSize={style.fontSize} mb="1rem">Last Name</Field.Label>
                        <Input {...register("last_name")} size="xl" fontSize="1.3rem" bg="white"/>
                        <Field.ErrorText>{errors.lastName?.message}</Field.ErrorText>
                    </Field.Root>

                    <Field.Root  invalid={!!errors.email} required>
                        <Field.Label fontSize={style.fontSize} mb="1rem">
                            Email
                            <Field.RequiredIndicator/>
                        </Field.Label>
                        <Input {...register("email")} size="xl" fontSize="1.3rem" bg="white"/>
                        <Field.ErrorText>{errors.email?.message}</Field.ErrorText>
                    </Field.Root>

                    <Field.Root  invalid={!!errors.password} required>
                        <Field.Label fontSize={style.fontSize} mb="1rem">
                            Password
                            <Field.RequiredIndicator/>
                        </Field.Label>
                        <PasswordInput {...register("password")} size="xl" fontSize="1.3rem" bg="white"/>
                        <Field.ErrorText>{errors.password?.message}</Field.ErrorText>
                    </Field.Root>

                    <Field.Root  invalid={!!errors.confirmedPassword} required>
                        <Field.Label fontSize={style.fontSize} mb="1rem">
                            Confirmed Password
                            <Field.RequiredIndicator/>
                        </Field.Label>
                        <PasswordInput {...register("confirmedPassword")} size="xl" fontSize="1.3rem" bg="white"/>
                        <Field.ErrorText>{errors.confirmedPassword?.message}</Field.ErrorText>
                    </Field.Root>

                    <Button type="submit" alignSelf="center" bg="green.800" color="white" h="3rem" w="8rem" _hover={{bg: "green.600"}} fontSize={style.fontSize}>Sign up</Button>

                </Flex>      
            </form>
        </Box>
    );
}