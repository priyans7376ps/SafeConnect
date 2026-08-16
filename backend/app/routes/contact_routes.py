from flask import Blueprint, g, request

from app.extensions import db
from app.models.trusted_contact import TrustedContact
from app.utils.decorators import jwt_required_custom
from app.utils.helpers import error_response, success_response
from app.utils.validators import validate_email, validate_phone

contact_bp = Blueprint("contacts", __name__)


@contact_bp.route("/contacts", methods=["GET"])
@jwt_required_custom
def get_contacts():
    contacts = TrustedContact.query.filter_by(user_id=int(g.current_user_id)).order_by(TrustedContact.created_at.desc()).all()
    return success_response("Contacts retrieved", {"contacts": [item.to_dict() for item in contacts]})


@contact_bp.route("/contacts", methods=["POST"])
@jwt_required_custom
def create_contact():
    user_id = int(g.current_user_id)
    data = request.get_json(silent=True) or {}
    try:
        name = (data.get("name") or "").strip()
        if not name:
            raise ValueError("Name is required")
        phone = validate_phone(data.get("phone"))
        email = data.get("email")
        if email:
            email = validate_email(email)
        relationship = (data.get("relationship") or "").strip()
        if not relationship:
            raise ValueError("Relationship is required")

        contact = TrustedContact(
            user_id=user_id,
            name=name,
            phone=phone,
            email=email,
            relationship=relationship,
            is_primary=bool(data.get("is_primary", False)),
        )
        db.session.add(contact)
        db.session.commit()
        return success_response("Contact created", {"contact": contact.to_dict()}, 201)
    except ValueError as exc:
        return error_response(str(exc), 400)
    except Exception:
        db.session.rollback()
        return error_response("Unable to create contact", 500)


@contact_bp.route("/contacts/<int:contact_id>", methods=["PUT"])
@jwt_required_custom
def update_contact(contact_id):
    contact = TrustedContact.query.filter_by(id=contact_id, user_id=int(g.current_user_id)).first()
    if not contact:
        return error_response("Contact not found", 404)

    data = request.get_json(silent=True) or {}
    try:
        if "name" in data and data["name"] is not None:
            contact.name = str(data["name"]).strip()
        if "phone" in data and data["phone"] is not None:
            contact.phone = validate_phone(data["phone"])
        if "email" in data and data["email"] is not None:
            contact.email = validate_email(data["email"])
        if "relationship" in data and data["relationship"] is not None:
            contact.relationship = str(data["relationship"]).strip()
        if "is_primary" in data:
            contact.is_primary = bool(data["is_primary"])
        db.session.commit()
        return success_response("Contact updated", {"contact": contact.to_dict()})
    except ValueError as exc:
        return error_response(str(exc), 400)
    except Exception:
        db.session.rollback()
        return error_response("Unable to update contact", 500)


@contact_bp.route("/contacts/<int:contact_id>", methods=["DELETE"])
@jwt_required_custom
def delete_contact(contact_id):
    contact = TrustedContact.query.filter_by(id=contact_id, user_id=int(g.current_user_id)).first()
    if not contact:
        return error_response("Contact not found", 404)
    db.session.delete(contact)
    db.session.commit()
    return success_response("Contact deleted")
