from pydantic import BaseModel
from typing import Optional, List, Any

class PlatformType(BaseModel):
    pass

class Attendees(BaseModel):
    id: Optional[int]
    name: Optional[str]
    email: Optional[str]

class UserProfileImage(BaseModel):
    userId: int
    imageBinary: Optional[str]

class VerificationRequest(BaseModel):
    name: Optional[str]
    value: Optional[str]
    type: Any

class VerificationType(BaseModel):
    pass

class BaseUser(BaseModel):
    id: int
    userName: Optional[str]
    email: Optional[str]
    firstName: Optional[str]
    lastName: Optional[str]
    addressLine1: Optional[str]
    addressLine2: Optional[str]
    phoneNumber: Optional[str]
    state: Optional[str]
    country: Optional[str]
    city: Optional[str]
    pinCode: Optional[str]
    roleId: int
    memberId: Optional[int]
    memberRelationUserId: Optional[int]
    memberRelationUniqueId: Optional[str]
    memberUserRelationshipId: Optional[int]

class EventDTO(BaseModel):
    eventId: Optional[int]
    title: Optional[str]
    details: Optional[str]
    startTime: str
    endTime: str
    createdBy: int
    attendees: Optional[List[Attendees]]
    externalUsers: Optional[List[Attendees]]

class MemberDTO(BaseModel):
    memberId: Optional[int]
    email: Optional[str]
    firstName: Optional[str]
    lastName: Optional[str]
    addressLine1: Optional[str]
    addressLine2: Optional[str]
    phoneNumber: Optional[str]
    state: Optional[str]
    country: Optional[str]
    city: Optional[str]
    pinCode: Optional[str]
    userId: int
    relationshipId: int

class MessageRequest(BaseModel):
    pageSize: int
    pageNumber: int
    receiverId: int
    senderId: int

class TokenResponse(BaseModel):
    access_token: Optional[str]
    refresh_token: Optional[str]
    expires_in: int
    uniqueId: Optional[str]

class User(BaseModel):
    id: int
    userName: Optional[str]
    email: Optional[str]
    firstName: Optional[str]
    lastName: Optional[str]
    addressLine1: Optional[str]
    addressLine2: Optional[str]
    phoneNumber: Optional[str]
    state: Optional[str]
    country: Optional[str]
    city: Optional[str]
    pinCode: Optional[str]
    roleId: int
    memberId: Optional[int]
    memberRelationUserId: Optional[int]
    memberRelationUniqueId: Optional[str]
    memberUserRelationshipId: Optional[int]
    password: Optional[str]

class UserCred(BaseModel):
    username: Optional[str]
    password: Optional[str]

class UserDeviceDTO(BaseModel):
    userId: int
    deviceToken: Optional[str]
    platform: Any

class UserMemberDto(BaseModel):
    userId: int
    uniqueMatchID: Optional[str]
    name: Optional[str]
    memberEmail: Optional[str]
    memberName: Optional[str]
    memberId: int
