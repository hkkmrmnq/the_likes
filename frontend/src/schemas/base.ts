import { z } from "zod";
import { CONSTANTS as CNST } from "@/src/config";

export const dataTimeShchema = z.string().datetime(); // .iso.datetime(): next.js build error
export const timeSchema = z.string().time(); // z.iso.time(): next.js build error
export const uuidSchema = z.uuid();
export const messageTextSchema = z.string().max(CNST.MESSAGE_MAX_LENGTH);
