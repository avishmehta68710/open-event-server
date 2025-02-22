from app.api.helpers.db import save_to_db
from app.api.helpers.files import make_frontend_url
from app.api.helpers.log import record_activity
from app.api.helpers.system_notifications import (
    NOTIFS,
    get_event_exported_actions,
    get_event_imported_actions,
    get_event_role_notification_actions,
    get_monthly_payment_notification_actions,
    get_new_session_notification_actions,
    get_session_state_change_notification_actions,
    get_ticket_purchased_attendee_notification_actions,
    get_ticket_purchased_notification_actions,
    get_ticket_purchased_organizer_notification_actions,
)
from app.models.notification import (
    AFTER_EVENT,
    EVENT_EXPORT_FAIL,
    EVENT_EXPORTED,
    EVENT_IMPORT_FAIL,
    EVENT_IMPORTED,
    EVENT_ROLE,
    MONTHLY_PAYMENT_FOLLOWUP_NOTIF,
    MONTHLY_PAYMENT_NOTIF,
    NEW_SESSION,
    SESSION_STATE_CHANGE,
    TICKET_CANCELLED,
    TICKET_CANCELLED_ORGANIZER,
    TICKET_PURCHASED,
    TICKET_PURCHASED_ATTENDEE,
    TICKET_PURCHASED_ORGANIZER,
    Notification,
)


def send_notification(user, title, message, actions=None):
    """
    Helper function to send notifications.
    :param user:
    :param title:
    :param message:
    :param actions:
    :return:
    """
    notification = Notification(user_id=user.id, title=title, message=message)
    if not actions:
        actions = []
    notification.actions = actions
    save_to_db(notification, msg="Notification saved")
    record_activity('notification_event', user=user, title=title, actions=actions)


def send_notif_new_session_organizer(user, event_name, link, session_id):
    """
    Send notification to the event organizer about a new session.
    :param user:
    :param event_name:
    :param link:
    :param session_id:
    :return:
    """
    actions = get_new_session_notification_actions(session_id, link)
    notification = NOTIFS[NEW_SESSION]
    title = notification['title'].format(event_name=event_name)
    message = notification['message'].format(event_name=event_name, link=link)

    send_notification(user, title, message, actions)


def send_notif_session_state_change(user, session_name, acceptance, link, session_id):
    """
    Send notification to the session creator about a session status being changed.
    :param user:
    :param session_name:
    :param acceptance:
    :param link:
    :param session_id:
    :return:
    """
    actions = get_session_state_change_notification_actions(session_id, link)
    notification = NOTIFS[SESSION_STATE_CHANGE]
    title = notification['title'].format(session_name=session_name, acceptance=acceptance)
    message = notification['message'].format(
        session_name=session_name, acceptance=acceptance
    )

    send_notification(user, title, message, actions)


def send_notif_after_import(
    user, event_id=None, event_name=None, event_url=None, error_text=None
):
    """send notification after event import"""
    if error_text:
        send_notification(
            user=user,
            title=NOTIFS[EVENT_IMPORT_FAIL]['title'].format(event_name=event_name),
            message=NOTIFS[EVENT_IMPORT_FAIL]['message'].format(error_text=error_text),
        )
    elif event_name:
        actions = get_event_imported_actions(event_id, event_url)
        send_notification(
            user=user,
            title=NOTIFS[EVENT_IMPORTED]['title'].format(event_name=event_name),
            message=NOTIFS[EVENT_IMPORTED]['message'].format(
                event_name=event_name, event_url=event_url
            ),
            actions=actions,
        )


def send_notif_after_export(user, event_name, download_url=None, error_text=None):
    """send notification after event export"""
    if error_text:
        send_notification(
            user=user,
            title=NOTIFS[EVENT_EXPORT_FAIL]['title'].format(event_name=event_name),
            message=NOTIFS[EVENT_EXPORT_FAIL]['message'].format(error_text=error_text),
        )
    elif download_url:
        actions = get_event_exported_actions(download_url)
        send_notification(
            user=user,
            title=NOTIFS[EVENT_EXPORTED]['title'].format(event_name=event_name),
            message=NOTIFS[EVENT_EXPORTED]['message'].format(
                event_name=event_name, download_url=download_url
            ),
            actions=actions,
        )


def send_notif_monthly_fee_payment(
    user, event_name, previous_month, amount, app_name, link, event_id, follow_up=False
):
    """
    Send notification about monthly fee payments.
    :param user:
    :param event_name:
    :param previous_month:
    :param amount:
    :param app_name:
    :param link:
    :param event_id:
    :return:
    """
    key = MONTHLY_PAYMENT_FOLLOWUP_NOTIF if follow_up else MONTHLY_PAYMENT_NOTIF
    actions = get_monthly_payment_notification_actions(event_id, link)
    notification = NOTIFS[key]
    title = notification['subject'].format(date=previous_month, event_name=event_name)
    message = notification['message'].format(
        event_name=event_name,
        date=previous_month,
        amount=amount,
        app_name=app_name,
    )

    send_notification(user, title, message, actions)


def send_notif_event_role(user, role_name, event_name, link, event_id):
    """
    Send notification to a user about an event role invite.
    :param user:
    :param role_name:
    :param event_name:
    :param link:
    :param event_id:
    :return:
    """
    actions = get_event_role_notification_actions(event_id, link)
    notification = NOTIFS[EVENT_ROLE]
    title = notification['title'].format(role_name=role_name, event_name=event_name)
    message = notification['message'].format(
        role_name=role_name, event_name=event_name, link=link
    )

    send_notification(user, title, message, actions)


def send_notif_after_event(user, event_name):
    """
    Send notification to a user after the conclusion of an event.
    :param user:
    :param event_name:
    :return:
    """
    notif = NOTIFS[AFTER_EVENT]
    title = notif['title'].format(event_name=event_name)
    message = notif['message'].format(event_name=event_name)

    send_notification(user, title, message)


def send_notif_ticket_purchase_organizer(user, order):
    """Send notification with order invoice link after purchase"""
    actions = get_ticket_purchased_organizer_notification_actions(
        order.identifier, order.site_view_link
    )
    send_notification(
        user=user,
        title=NOTIFS[TICKET_PURCHASED_ORGANIZER]['title'].format(
            invoice_id=order.invoice_number, event_name=order.event.name
        ),
        message=NOTIFS[TICKET_PURCHASED_ORGANIZER]['message'],
        actions=actions,
    )


def send_notif_to_attendees(order):
    """
    Send notification to attendees of an order.
    :param order:
    :return:
    """
    for holder in order.ticket_holders:
        if holder.user:
            # send notification if the ticket holder is a registered user.
            if holder.user.id != order.user_id:
                # The ticket holder is not the purchaser
                actions = get_ticket_purchased_attendee_notification_actions(
                    holder.pdf_url
                )
                send_notification(
                    user=holder.user,
                    title=NOTIFS[TICKET_PURCHASED_ATTENDEE]['title'].format(
                        event_name=order.event.name
                    ),
                    message=NOTIFS[TICKET_PURCHASED_ATTENDEE]['message'],
                    actions=actions,
                )
            else:
                # The Ticket purchaser
                actions = get_ticket_purchased_notification_actions(
                    order.id, order.tickets_pdf_url
                )
                send_notification(
                    user=holder.user,
                    title=NOTIFS[TICKET_PURCHASED]['title'].format(
                        invoice_id=order.invoice_number
                    ),
                    message=NOTIFS[TICKET_PURCHASED]['message'],
                    actions=actions,
                )


def send_notif_ticket_cancel(order):
    """Send notification with order invoice link after cancel"""
    send_notification(
        user=order.user,
        title=NOTIFS[TICKET_CANCELLED]['title'].format(
            invoice_id=order.invoice_number, event_name=order.event.name
        ),
        message=NOTIFS[TICKET_CANCELLED]['message'].format(
            cancel_note=order.cancel_note,
            event_name=order.event.name,
            event_url=make_frontend_url(f'/e/{order.event.identifier}'),
            order_url=make_frontend_url(f'/orders/{order.identifier}/view'),
            invoice_id=order.invoice_number,
        ),
    )
    for organizer in order.event.organizers:
        send_notification(
            user=organizer,
            title=NOTIFS[TICKET_CANCELLED_ORGANIZER]['title'].format(
                invoice_id=order.invoice_number, event_name=order.event.name
            ),
            message=NOTIFS[TICKET_CANCELLED_ORGANIZER]['message'].format(
                cancel_note=order.cancel_note,
                invoice_id=order.invoice_number,
                event_name=order.event.name,
                cancel_order_page=make_frontend_url(
                    '/events/{identifier}/tickets/orders/cancelled'.format(
                        identifier=order.event.identifier
                    )
                ),
            ),
        )
    send_notification(
        user=order.event.owner,
        title=NOTIFS[TICKET_CANCELLED_ORGANIZER]['title'].format(
            invoice_id=order.invoice_number, event_name=order.event.name
        ),
        message=NOTIFS[TICKET_CANCELLED_ORGANIZER]['message'].format(
            cancel_note=order.cancel_note,
            invoice_id=order.invoice_number,
            event_name=order.event.name,
            cancel_order_page=make_frontend_url(
                '/events/{identifier}/tickets/orders/cancelled'.format(
                    identifier=order.event.identifier
                )
            ),
        ),
    )


def send_notification_with_action(user, action, **kwargs):
    """
    A general notif helper to use in auth APIs
    :param user: user to which notification is to be sent
    :param action:
    :param kwargs:
    :return:
    """

    send_notification(
        user=user,
        title=NOTIFS[action]['subject'].format(**kwargs),
        message=NOTIFS[action]['message'].format(**kwargs),
    )
