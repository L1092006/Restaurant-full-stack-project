import { Box, Field, Input, Button, Flex } from "@chakra-ui/react";
import { toaster } from "../components/ui/toaster";
import { PasswordInput } from "../components/ui/password-input";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import  { useForm } from "react-hook-form";
import { Link } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { useNavigate } from "react-router-dom";


// Define the schema for the form
const schema = z.object({
    username: z.string().min(1, "This can not be empty"),
    password: z.string().min(1, "This can not be empty")

})

export default function Login() {
    const {
        register,
        handleSubmit,
        formState: { errors }
    } = useForm({ resolver: zodResolver(schema), mode: "onChange"});

    const navigate = useNavigate();

    const { login } = useAuth();

    //FIXME: improve the handler if needed
    const mySubmitHandler = async (data) => {
        const success = await login(data.username, data.password);
        if(success) navigate('/');
        else {
            console.log('here');
            toaster.create({
                title: "Error",
                description: "Invalid username or password",
                type: "error",
                closable: true
            });
        }
        
    }

    const style = {
        color: "gray.700",
        font: "cursive",
        fontSize: "1.5rem",
        gap: "3rem",
        buttonH: "3rem",
        buttonW: "8rem"
    }

    return (
        <Box mt="10vh" color={style.color} fontFamily="cursive" w="70vw" mx="auto">
            <form onSubmit={handleSubmit(mySubmitHandler)}>
                <Flex direction="column" gap={style.gap}>
                    <Field.Root invalid={!!errors.username}>
                        <Field.Label fontSize={style.fontSize} mb="1rem">Username</Field.Label>
                        <Input {...register("username")} size="xl" fontSize="1.3rem" bg="white"/>
                        <Field.ErrorText>{errors.username?.message}</Field.ErrorText>
                    </Field.Root>

                    <Field.Root  invalid={!!errors.password} fontSize={style.fontSize}>
                        <Field.Label fontSize={style.fontSize} mb="1rem">Password</Field.Label>
                        <PasswordInput {...register("password")} size="xl" fontSize="1.3rem" bg="white"/>
                        <Field.ErrorText>{errors.password?.message}</Field.ErrorText>
                    </Field.Root>

                    <Button type="submit" alignSelf="center" bg="green.800" color="white" h="3rem" w="8rem" _hover={{bg: "green.600"}} fontSize={style.fontSize}>Submit</Button>

                    <Button as={Link} to="/signup" color="gray.700" fontSize="0.8rem" w="15rem">No Account? Sign up here!</Button>

                </Flex>      
            </form>
        </Box>
    )
}